from __future__ import annotations

import logging
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from backend.infrastructure.config import Settings
from backend.interfaces.download_clients import qbittorrent
from backend.web.page import render_page

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
@router.get("/index.html", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    qs = dict(request.query_params)
    tab = qs.get("tab", "downloads")
    stab = qs.get("stab", "")
    msg = qs.get("msg", "")
    return HTMLResponse(render_page(Settings.load(), msg, tab, stab))


@router.get("/sources")
def sources_redirect() -> RedirectResponse:
    return RedirectResponse("/?tab=sources", status_code=303)


@router.get("/settings")
def settings_redirect(request: Request) -> RedirectResponse:
    tab = request.query_params.get("tab", "")
    location = f"/?tab=settings&stab={tab}" if tab else "/?tab=settings"
    return RedirectResponse(location, status_code=303)


@router.get("/api/config")
def api_config() -> JSONResponse:
    return JSONResponse(Settings.load().to_config_dict())


@router.get("/api/jobs")
def api_jobs() -> JSONResponse:
    return JSONResponse({"jobs": qbittorrent.torrents_info(Settings.load())})
