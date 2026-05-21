from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time

# ─── Session store (persisted to disk so restarts don't invalidate cookies) ───

SESSION_TTL = 86400 * 30           # 30 days
COOKIE_NAME = "deceptarr_session"

def _sessions_path() -> str:
    config = os.getenv("CONFIG_PATH", "").strip() or "/config/config.json"
    return os.path.join(os.path.dirname(config), "sessions.json")

def _load() -> dict[str, float]:
    try:
        with open(_sessions_path(), "r", encoding="utf-8") as f:
            raw: dict = json.load(f)
        now = time.time()
        return {k: v for k, v in raw.items() if isinstance(v, (int, float)) and v > now}
    except Exception:
        return {}

def _save(sessions: dict[str, float]) -> None:
    try:
        path = _sessions_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sessions, f)
    except Exception:
        pass

_sessions: dict[str, float] = _load()   # token → expiry timestamp


# ─── Password hashing (PBKDF2-SHA256, 260 000 iterations) ────────────────────

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"pbkdf2:sha256:260000:{salt}:{dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, algo, iters_s, salt, expected = stored.split(":", 4)
        dk = hashlib.pbkdf2_hmac(algo, password.encode(), salt.encode(), int(iters_s))
        return hmac.compare_digest(dk.hex(), expected)
    except Exception:
        return False


# ─── Session helpers ──────────────────────────────────────────────────────────

def create_session() -> str:
    token = secrets.token_hex(32)
    _sessions[token] = time.time() + SESSION_TTL
    _save(_sessions)
    return token


def verify_session(token: str) -> bool:
    exp = _sessions.get(token)
    if exp is None:
        return False
    if time.time() > exp:
        del _sessions[token]
        _save(_sessions)
        return False
    return True


def delete_session(token: str) -> None:
    _sessions.pop(token, None)
    _save(_sessions)
