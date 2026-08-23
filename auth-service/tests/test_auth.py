import os
os.environ["DATABASE_URL"] = "postgresql://testuser:testpass@localhost:5437/testdb"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200


def test_register_and_login():
    response = client.post("/register", json={
        "username": "chatuser1",
        "email": "chatuser1@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert response.json()["username"] == "chatuser1"

    response = client.post("/login", data={
        "username": "chatuser1",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_token_contains_user_id():
    client.post("/register", json={
        "username": "tokencheckuser",
        "email": "tokencheck@example.com",
        "password": "testpass123"
    })
    response = client.post("/login", data={
        "username": "tokencheckuser",
        "password": "testpass123"
    })
    token = response.json()["access_token"]

    from jose import jwt
    payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
    assert payload["sub"] == "tokencheckuser"
    assert "user_id" in payload


def test_duplicate_registration_fails():
    client.post("/register", json={
        "username": "dupechat",
        "email": "dupechat1@example.com",
        "password": "testpass123"
    })
    response = client.post("/register", json={
        "username": "dupechat",
        "email": "dupechat2@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 400
