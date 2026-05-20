from __future__ import annotations

import hashlib
import hmac
import secrets
import time

# ─── In-memory session store ──────────────────────────────────────────────────

_sessions: dict[str, float] = {}   # token → expiry timestamp
SESSION_TTL = 86400 * 30           # 30 days
COOKIE_NAME = "deceptarr_session"


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
    return token


def verify_session(token: str) -> bool:
    exp = _sessions.get(token)
    if exp is None:
        return False
    if time.time() > exp:
        del _sessions[token]
        return False
    return True


def delete_session(token: str) -> None:
    _sessions.pop(token, None)
