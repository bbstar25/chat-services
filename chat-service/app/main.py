import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.auth import decode_token
from app.redis_client import redis_client
from app.database import engine, get_db, Base, SessionLocal
from app import models, schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chat Service")

active_connections: dict[str, dict[str, WebSocket]] = {}


async def redis_listener():
    """Runs for the lifetime of the app, listening to ALL room events from Redis
    and broadcasting them to this instance's own locally-connected clients."""
    pubsub = redis_client.pubsub()
    pubsub.psubscribe("chat_events:*")
    print("redis_listener: subscribed and running", flush=True)

    loop = asyncio.get_event_loop()

    while True:
        message = await loop.run_in_executor(None, pubsub.get_message, True, 1.0)
        if message is None or message["type"] != "pmessage":
            continue

        event = json.loads(message["data"])
        room = event.get("room")
        if not room or room not in active_connections:
            continue

        for conn in list(active_connections[room].values()):
            try:
                await conn.send_text(json.dumps(event))
            except Exception:
                pass


@app.on_event("startup")
async def start_redis_listener():
    asyncio.create_task(redis_listener())


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/history/{room}", response_model=list[schemas.MessageOut])
def get_history(room: str, limit: int = 50, db: Session = Depends(get_db)):
    messages = (
        db.query(models.Message)
        .filter(models.Message.room == room)
        .order_by(desc(models.Message.created_at))
        .limit(limit)
        .all()
    )
    return list(reversed(messages))


@app.websocket("/ws/chat/{room}")
async def chat_websocket(websocket: WebSocket, room: str, token: str = Query(...), db: Session = Depends(get_db)):
    payload = decode_token(token)
    if payload is None:
        await websocket.close(code=1008)
        return

    username = payload.get("sub")
    await websocket.accept()

    if room not in active_connections:
        active_connections[room] = {}
    active_connections[room][username] = websocket

    channel = f"chat_events:{room}"
    redis_client.publish(channel, json.dumps({
        "type": "user_joined", "room": room, "username": username
    }))

    try:
        while True:
            data = await websocket.receive_text()

            new_message = models.Message(room=room, username=username, content=data)
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            message_event = {
                "type": "message",
                "room": room,
                "username": username,
                "content": data,
                "id": new_message.id,
                "created_at": new_message.created_at.isoformat()
            }

            # NOTE: no direct local broadcast here anymore — publish only.
            # The redis_listener() background task delivers it to all instances,
            # including this one, keeping every instance's behavior identical.
            redis_client.publish(channel, json.dumps(message_event))

    except WebSocketDisconnect:
        del active_connections[room][username]
        redis_client.publish(channel, json.dumps({
            "type": "user_left", "room": room, "username": username
        }))
