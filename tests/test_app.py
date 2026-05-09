from secrets import token_hex

from backend.app.main import app
from fastapi.testclient import TestClient


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login():
    email = f"friend-{token_hex(4)}@example.com"
    with TestClient(app) as client:
        register = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "safe-password-123",
                "display_name": "Friend",
            },
        )
        assert register.status_code == 201
        assert "access_token" in register.json()

        login = client.post(
            "/api/auth/login",
            json={"email": email, "password": "safe-password-123"},
        )
        assert login.status_code == 200
        assert "access_token" in login.json()
