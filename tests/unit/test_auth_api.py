import pytest
from fastapi.testclient import TestClient

from main import app


def test_register_and_login_flow(db_session, fake_user_data):
    client = TestClient(app)

    payload = {
        "fname": fake_user_data["first_name"],
        "lname": fake_user_data["last_name"],
        "email": fake_user_data["email"],
        "username": fake_user_data["username"],
        "password": "TestPass123"
    }

    # Register
    r = client.post("/register", json=payload)
    assert r.status_code == 200
    assert r.json().get("message") == "User registered successfully"

    # Login
    login_payload = {"username": payload["username"], "password": payload["password"]}
    r2 = client.post("/login", json=login_payload)
    assert r2.status_code == 200
    assert "token" in r2.json()


def test_register_duplicate_returns_error(db_session, fake_user_data):
    client = TestClient(app)

    payload = {
        "fname": fake_user_data["first_name"],
        "lname": fake_user_data["last_name"],
        "email": fake_user_data["email"],
        "username": fake_user_data["username"],
        "password": "TestPass123"
    }

    r1 = client.post("/register", json=payload)
    assert r1.status_code == 200

    # second registration should fail (server currently returns 500 on ValueError)
    r2 = client.post("/register", json=payload)
    assert r2.status_code >= 400


def test_login_invalid_credentials(db_session, fake_user_data):
    client = TestClient(app)

    payload = {
        "fname": fake_user_data["first_name"],
        "lname": fake_user_data["last_name"],
        "email": fake_user_data["email"],
        "username": fake_user_data["username"],
        "password": "TestPass123"
    }

    # register the user
    r = client.post("/register", json=payload)
    assert r.status_code == 200

    # attempt login with wrong password
    r2 = client.post("/login", json={"username": payload["username"], "password": "WrongPass"})
    assert r2.status_code == 401
