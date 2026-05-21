from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, RedirectResponse, Response

from backend.infrastructure.config import Settings, save_settings
from backend.interfaces.download_clients import qbittorrent
from backend.api.forms import form_to_config, parse_multipart, read_urlencoded, test_connection, test_connections

log = logging.getLogger(__name__)
router = APIRouter()

_OK = PlainTextResponse("Ok.\n")


def _section_redirect(section: str) -> RedirectResponse:
    if section in {"radarr", "sonarr", "worker", "tasks", "indexer", "downloader", "jellyfin", "runtime"}:
        return RedirectResponse(f"/?tab=settings&stab={section}", status_code=303)
    if section == "sources":
        return RedirectResponse("/?tab=sources", status_code=303)
    return RedirectResponse("/", status_code=303)


def _read_form(body: bytes, content_type: str) -> dict[str, str]:
    if content_type.startswith("multipart/form-data"):
        return parse_multipart(body, content_type)
    return read_urlencoded(body)


@router.post("/save")
async def save(request: Request) -> RedirectResponse:
    body = await request.body()
    form = _read_form(body, request.headers.get("content-type", ""))
    section = form.get("_section", "radarr")
    settings = Settings.load()
    try:
        data = form_to_config(form, settings)
        save_settings(data, settings.config_path)
    except Exception:
        log.exception("Save failed")
    return _section_redirect(section)


@router.post("/test")
async def test_conn(request: Request) -> RedirectResponse:
    body = await request.body()
    form = _read_form(body, request.headers.get("content-type", ""))
    section = form.get("_section", "radarr")
    settings = Settings.load()
    if section == "radarr":
        test_connection("Radarr", settings.radarr_url, settings.radarr_api_key)
    elif section == "sonarr":
        test_connection("Sonarr", settings.sonarr_url, settings.sonarr_api_key)
    else:
        test_connections(settings)
    return RedirectResponse(f"/?tab=settings&stab={section}", status_code=303)


@router.post("/tasks/bulk", response_model=None)
async def tasks_bulk(request: Request) -> Response:
    body = await request.body()
    form = _read_form(body, request.headers.get("content-type", ""))
    settings = Settings.load()
    action = form.get("action", "")
    from backend.infrastructure.jobs import JobStore
    store = JobStore(settings.state_path)
    jobs = store.list_jobs()
    if action == "resume_all":
        hashes = ",".join(
            j.job_id
            for j in jobs
            if j.paused or j.status in {"error", "queued", "running"}
        )
        if hashes:
            qbittorrent.pause(settings, hashes, False)
    elif action == "pause_all":
        hashes = ",".join(j.job_id for j in jobs if j.status in {"running", "queued"} and not j.paused)
        if hashes:
            qbittorrent.pause(settings, hashes, True)
    elif action == "clear_done":
        hashes = ",".join(j.job_id for j in jobs if j.status == "completed")
        if hashes:
            qbittorrent.delete(settings, hashes)
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse("/", status_code=303)
    return _OK


@router.post("/tasks/action", response_model=None)
async def tasks_action(request: Request) -> Response:
    body = await request.body()
    form = _read_form(body, request.headers.get("content-type", ""))
    settings = Settings.load()
    action = form.get("action", "")
    hashes = form.get("hashes", "")
    if action == "resume":
        qbittorrent.pause(settings, hashes, False)
    elif action == "pause":
        qbittorrent.pause(settings, hashes, True)
    elif action == "delete":
        qbittorrent.delete(settings, hashes)
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse("/", status_code=303)
    return _OK
