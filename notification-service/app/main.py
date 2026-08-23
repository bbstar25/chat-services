import json
import time
from app.redis_client import redis_client


def handle_event(event: dict):
    event_type = event.get("type")

    if event_type == "user_joined":
        print(f"[NOTIFY] {event['username']} joined the chat")
    elif event_type == "user_left":
        print(f"[NOTIFY] {event['username']} left the chat")
    elif event_type == "message":
        print(f"[NOTIFY] New message from {event['username']}: {event['content']}")
    else:
        print(f"[NOTIFY] Unknown event: {event}")


def main():
    print("Notification service starting, waiting for Redis...")
    time.sleep(3)  # simple wait, gives Redis time to be ready on first startup

    pubsub = redis_client.pubsub()
    pubsub.psubscribe("chat_events:*")
    print("Subscribed to chat_events:* (all rooms), listening...")

    for message in pubsub.listen():
        if message["type"] != "pmessage":
            continue  # skip Redis's own subscription-confirmation messages
        event = json.loads(message["data"])
        handle_event(event)


if __name__ == "__main__":
    main()

