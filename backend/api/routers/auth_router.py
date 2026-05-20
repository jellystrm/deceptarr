from __future__ import annotations

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from backend.infrastructure.auth import (
    COOKIE_NAME, SESSION_TTL,
    hash_password, verify_password,
    create_session, verify_session, delete_session,
)
from backend.infrastructure.config import Settings, save_settings

router = APIRouter()


@router.get("/api/auth/status")
def auth_status(request: Request) -> JSONResponse:
    settings = Settings.load()
    initialized = bool(settings.auth_username and settings.auth_password_hash)
    if not initialized:
        return JSONResponse({"initialized": False, "authenticated": False})
    token = request.cookies.get(COOKIE_NAME)
    authenticated = bool(token and verify_session(token))
    return JSONResponse({"initialized": True, "authenticated": authenticated})


@router.post("/api/auth/setup")
async def auth_setup(request: Request) -> JSONResponse:
    """First-time account creation. Returns 400 if already initialized."""
    settings = Settings.load()
    if settings.auth_username and settings.auth_password_hash:
        return JSONResponse({"error": "Already initialized"}, status_code=400)
    data = await request.json()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    if not username:
        return JSONResponse({"error": "Username is required"}, status_code=400)
    if len(password) < 4:
        return JSONResponse({"error": "Password must be at least 4 characters"}, status_code=400)
    config_data = settings.to_config_dict()
    config_data["auth_username"] = username
    config_data["auth_password_hash"] = hash_password(password)
    save_settings(config_data, settings.config_path)
    token = create_session()
    response = JSONResponse({"status": "ok"})
    response.set_cookie(COOKIE_NAME, token, httponly=True, max_age=SESSION_TTL, samesite="lax")
    return response


@router.post("/api/auth/login")
async def auth_login(request: Request) -> JSONResponse:
    settings = Settings.load()
    if not settings.auth_username or not settings.auth_password_hash:
        return JSONResponse({"error": "Not initialized"}, status_code=400)
    data = await request.json()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    if username != settings.auth_username or not verify_password(password, settings.auth_password_hash):
        return JSONResponse({"error": "Invalid username or password"}, status_code=401)
    token = create_session()
    response = JSONResponse({"status": "ok"})
    response.set_cookie(COOKIE_NAME, token, httponly=True, max_age=SESSION_TTL, samesite="lax")
    return response


@router.post("/api/auth/logout")
def auth_logout(request: Request, response: Response) -> JSONResponse:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        delete_session(token)
    response.delete_cookie(COOKIE_NAME)
    return JSONResponse({"status": "ok"})
