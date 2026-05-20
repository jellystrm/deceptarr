from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response

from backend.infrastructure.config import Settings
from backend.interfaces.indexers.torznab import caps_response, search_response

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/torznab/api")
def torznab_api(request: Request) -> Response:
    settings = Settings.load()
    query: dict[str, list[str]] = {k: [v] for k, v in request.query_params.items()}
    api_key = query.get("apikey", [""])[0]
    if settings.torznab_api_key and api_key != settings.torznab_api_key:
        log.warning("Torznab request rejected: invalid API key")
        return Response(status_code=401)
    log.info(
        "Torznab request: t=%s q=%s tmdbid=%s tvdbid=%s season=%s ep=%s",
        query.get("t", ["search"])[0],
        query.get("q", [""])[0],
        query.get("tmdbid", [""])[0],
        query.get("tvdbid", [""])[0],
        query.get("season", [""])[0],
        query.get("ep", [""])[0],
    )
    body = caps_response() if query.get("t", ["search"])[0] == "caps" else search_response(settings, query)
    return Response(content=body, media_type="application/xml; charset=utf-8")
