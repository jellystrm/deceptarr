from __future__ import annotations

import logging

from fastapi import APIRouter, Response

from backend.application.grab_service import decode_release
from backend.infrastructure.config import Settings
from backend.application.torrent import make_grab_torrent

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/grab/{token:path}")
def grab_download(token: str) -> Response:
    """Return a minimal .torrent whose announce URL embeds the grab token.

    Radarr/Sonarr fetch this and then POST the bytes to /api/v2/torrents/add.
    We recover the original grab URL from the torrent's announce field there.
    """
    token = token.strip("/").split("?")[0]
    if not token:
        return Response(status_code=400, content="Missing grab token")
    try:
        release = decode_release(token)
    except Exception:
        log.warning("Invalid grab token: %r", token)
        return Response(status_code=400, content="Invalid grab token")
    settings = Settings.load()
    grab_url = f"{settings.public_base_url}/grab/{token}"
    torrent_bytes = make_grab_torrent(grab_url, release.title)
    safe_name = release.title.replace("/", "-").replace("\\", "-")[:80]
    return Response(
        content=torrent_bytes,
        media_type="application/x-bittorrent",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.torrent"'},
    )
