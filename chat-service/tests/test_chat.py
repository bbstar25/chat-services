import os
os.environ["DATABASE_URL"] = "postgresql://testuser:testpass@localhost:5438/testdb"
os.environ["REDIS_URL"] = "redis://localhost:6380"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.database import Base, engine

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)


def make_token(username="testuser", user_id=1):
    return jwt.encode({"sub": username, "user_id": user_id}, "test-secret-key", algorithm="HS256")


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200


def test_websocket_rejects_invalid_token():
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/chat/general?token=not-a-real-token") as websocket:
            websocket.receive_text()


def test_websocket_accepts_valid_token_and_saves_message():
    token = make_token()
    with client.websocket_connect(f"/ws/chat/general?token={token}") as websocket:
        websocket.send_text("hello from test")

    response = client.get("/history/general")
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 1
    assert messages[0]["content"] == "hello from test"


def test_history_returns_saved_messages():
    token = make_token(username="historyuser")
    with client.websocket_connect(f"/ws/chat/history-room?token={token}") as websocket:
        websocket.send_text("first message")

    response = client.get("/history/history-room")
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 1
    assert messages[0]["content"] == "first message"


def test_rooms_are_isolated():
    token = make_token(username="roomuser")
    with client.websocket_connect(f"/ws/chat/room-a?token={token}") as websocket:
        websocket.send_text("only in room a")

    response = client.get("/history/room-b")
    assert response.status_code == 200
    assert response.json() == []
