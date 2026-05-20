from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api import create_app
from backend.infrastructure.auth import COOKIE_NAME


def test_setup_sets_session_cookie_and_authenticates(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path / "config.json"))
    client = TestClient(create_app())

    response = client.post("/api/auth/setup", json={"username": "admin", "password": "secret"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert COOKIE_NAME in response.cookies
    assert client.get("/api/auth/status").json() == {"initialized": True, "authenticated": True}
    assert client.get("/api/config").status_code == 200


def test_login_sets_session_cookie_for_existing_account(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path / "config.json"))
    setup_client = TestClient(create_app())
    setup_client.post("/api/auth/setup", json={"username": "admin", "password": "secret"})

    client = TestClient(create_app())
    response = client.post("/api/auth/login", json={"username": "admin", "password": "secret"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert COOKIE_NAME in response.cookies
    assert client.get("/api/auth/status").json() == {"initialized": True, "authenticated": True}
    assert client.get("/api/config").status_code == 200


def test_login_error_returns_json_without_cookie(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path / "config.json"))
    setup_client = TestClient(create_app())
    setup_client.post("/api/auth/setup", json={"username": "admin", "password": "secret"})

    client = TestClient(create_app())
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid username or password"}
    assert COOKIE_NAME not in response.cookies
    assert client.get("/api/auth/status").json() == {"initialized": True, "authenticated": False}
    assert client.get("/api/config").status_code == 401
