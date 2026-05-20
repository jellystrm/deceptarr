from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, RedirectResponse, Response

from backend.application.grab_service import decode_release, encode_release, enqueue_from_url
from backend.infrastructure.config import Settings
from backend.api.forms import parse_multipart, read_urlencoded

log = logging.getLogger(__name__)
router = APIRouter()

_OK = PlainTextResponse("Ok.\n")


def _read_form(body: bytes, content_type: str) -> dict[str, str]:
    if content_type.startswith("multipart/form-data"):
        return parse_multipart(body, content_type)
    return read_urlencoded(body)


@router.post("/api/manual-grab", response_model=None)
async def manual_grab(request: Request) -> Response:
    body = await request.body()
    form = _read_form(body, request.headers.get("content-type", ""))
    settings = Settings.load()
    token = form.get("token", "").strip()
    if not token:
        return PlainTextResponse("Missing token", status_code=400)
    try:
        release = decode_release(token)
    except Exception:
        log.warning("manual-grab: invalid token %r", token[:40])
        return PlainTextResponse("Invalid token", status_code=400)
    from dataclasses import replace as _replace
    output_mode = form.get("output_mode", release.output_mode)
    container = form.get("container") or None
    new_release = _replace(release, output_mode=output_mode, container=container)  # type: ignore[arg-type]
    new_token = encode_release(new_release)
    grab_url = f"{settings.public_base_url}/grab/{new_token}"
    try:
        enqueue_from_url(settings, grab_url)
    except Exception:
        log.exception("manual-grab: enqueue failed for token=%r", token[:40])
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse("/", status_code=303)
    return _OK


@router.post("/api/manual-grab-bulk", response_model=None)
async def manual_grab_bulk(request: Request) -> Response:
    body = await request.body()
    form = _read_form(body, request.headers.get("content-type", ""))
    settings = Settings.load()
    tokens_raw = form.get("tokens", "[]")
    output_mode = form.get("output_mode", "strm")
    container = form.get("container") or None
    try:
        tokens = json.loads(tokens_raw)
    except Exception:
        return PlainTextResponse("Invalid tokens JSON", status_code=400)
    if not isinstance(tokens, list):
        return PlainTextResponse("tokens must be a JSON array", status_code=400)
    from dataclasses import replace as _replace
    for token in tokens:
        if not isinstance(token, str):
            continue
        try:
            release = decode_release(token)
            new_release = _replace(release, output_mode=output_mode, container=container)  # type: ignore[arg-type]
            new_token = encode_release(new_release)
            grab_url = f"{settings.public_base_url}/grab/{new_token}"
            enqueue_from_url(settings, grab_url)
        except Exception:
            log.exception("manual-grab-bulk: failed for token %r", token[:40])
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse("/", status_code=303)
    return _OK
