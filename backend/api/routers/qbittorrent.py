from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.application.grab_service import enqueue_from_url
from backend.infrastructure.config import Settings
from backend.interfaces.download_clients import qbittorrent
from backend.api.forms import parse_multipart, parse_multipart_files, read_urlencoded
from backend.application.torrent import extract_announce

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2")

_OK = PlainTextResponse("Ok.\n")


def _truthy(value: str | None) -> bool:
    return (value or "").lower() in {"true", "1", "yes", "on"}


@router.get("/app/version")
def app_version() -> PlainTextResponse:
    return PlainTextResponse("4.6.0\n")


@router.get("/app/webapiVersion")
def app_webapi_version() -> PlainTextResponse:
    return PlainTextResponse("2.8.0\n")


@router.get("/app/preferences")
def app_preferences() -> JSONResponse:
    return JSONResponse(qbittorrent.preferences(Settings.load()))


@router.get("/app/buildInfo")
def app_build_info() -> JSONResponse:
    return JSONResponse(qbittorrent.build_info())


@router.get("/torrents/categories")
def torrents_categories() -> JSONResponse:
    return JSONResponse(qbittorrent.categories(Settings.load()))


@router.get("/torrents/info")
def torrents_info(request: Request) -> JSONResponse:
    return JSONResponse(
        qbittorrent.torrents_info(
            Settings.load(),
            category=request.query_params.get("category") or None,
            hashes=request.query_params.get("hashes") or None,
        )
    )


@router.get("/torrents/properties")
def torrents_properties() -> JSONResponse:
    return JSONResponse({})


@router.get("/torrents/files")
def torrents_files() -> JSONResponse:
    return JSONResponse([])


@router.get("/sync/maindata")
def sync_maindata(request: Request) -> JSONResponse:
    return JSONResponse(
        qbittorrent.sync_maindata(
            Settings.load(),
            category=request.query_params.get("category") or None,
        )
    )


@router.get("/transfer/info")
def transfer_info() -> JSONResponse:
    return JSONResponse(qbittorrent.transfer_info())


@router.post("/auth/login")
async def auth_login(request: Request) -> Response:
    settings = Settings.load()
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = parse_multipart(body, content_type)
    else:
        form = read_urlencoded(body)
    got_user = form.get("username", "").strip()
    got_pass = form.get("password", "").strip()
    exp_user = (settings.qb_username or "").strip()
    exp_pass = (settings.qb_password or "").strip()
    log.info(
        "Download client login: got user=%r expected user=%r match=%s",
        got_user, exp_user, got_user == exp_user and got_pass == exp_pass,
    )
    if got_user != exp_user or got_pass != exp_pass:
        return PlainTextResponse("Fails.")
    return Response(
        content=b"Ok.",
        media_type="text/plain",
        headers={"Set-Cookie": "SID=deceptarr; HttpOnly; path=/"},
    )


@router.post("/torrents/add")
async def torrents_add(request: Request) -> Response:
    settings = Settings.load()
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = parse_multipart(body, content_type)
        files = parse_multipart_files(body, content_type)
    else:
        form = read_urlencoded(body)
        files = {}

    category = form.get("category", "deceptarr")
    paused = form.get("paused", "").lower() in {"true", "1", "yes", "on"}
    candidate_urls: list[str] = []

    torrent_bytes = files.get("torrents")
    if torrent_bytes:
        announce = extract_announce(torrent_bytes)
        if announce and "/grab/" in announce:
            log.debug("qbit add: extracted grab URL from torrent announce: %s", announce)
            candidate_urls.append(announce)
        else:
            log.warning("qbit add: torrent uploaded but no /grab/ announce URL found (announce=%r)", announce)

    urls_field = form.get("urls", "")
    for url in urls_field.replace("\r", "\n").split("\n"):
        url = url.strip()
        if url:
            candidate_urls.append(url)

    added = []
    for url in candidate_urls:
        try:
            job = enqueue_from_url(settings, url, category=category, paused=paused)
            added.append(job.job_id)
        except Exception:
            log.exception("qbit add: failed to enqueue %r", url)

    if not added:
        log.warning("Download client add rejected: no usable urls or torrents field")
        return Response(status_code=400, content="No supported urls field")

    log.info("Download client add accepted: category=%s paused=%s jobs=%s", category, paused, ",".join(added))
    from backend.infrastructure.jobs import JobStore
    from backend.infrastructure.activity import ActivityLog

    store = JobStore(settings.state_path)
    for job_id in added:
        job = store.get(job_id)
        if job:
            ActivityLog.get().add(
                kind="grab",
                title=job.release.title,
                detail=f"source={job.release.source_name or 'auto'}  mode={job.release.output_mode}",
                status="ok",
                ref=job_id,
            )
    return _OK


@router.post("/torrents/delete")
async def torrents_delete(request: Request) -> PlainTextResponse:
    body = await request.body()
    form = read_urlencoded(body)
    delete_files = _truthy(form.get("deleteFiles") or form.get("delete_files"))
    qbittorrent.delete(Settings.load(), form.get("hashes", ""), delete_files=delete_files)
    return _OK


@router.post("/torrents/pause")
async def torrents_pause(request: Request) -> PlainTextResponse:
    body = await request.body()
    form = read_urlencoded(body)
    qbittorrent.pause(Settings.load(), form.get("hashes", ""), True)
    return _OK


@router.post("/torrents/resume")
async def torrents_resume(request: Request) -> PlainTextResponse:
    body = await request.body()
    form = read_urlencoded(body)
    qbittorrent.pause(Settings.load(), form.get("hashes", ""), False)
    return _OK


@router.post("/torrents/setCategory")
@router.post("/torrents/createCategory")
@router.post("/torrents/editCategory")
@router.post("/torrents/removeCategories")
@router.post("/torrents/addTags")
@router.post("/torrents/removeTags")
def torrents_category_noop() -> PlainTextResponse:
    return _OK
