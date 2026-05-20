from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from backend.infrastructure.config import Settings

log = logging.getLogger(__name__)
router = APIRouter()


def _season_ep_count(tmdb_id: int | None, season: int, settings: Any) -> int | None:
    if not tmdb_id or not settings.tmdb_api_key:
        return None
    from backend.adapters.tmdb import TmdbClient
    try:
        info = TmdbClient(settings.tmdb_api_key).get_series_info(tmdb_id)
        for s in (info.seasons or []):
            if s.season_number == season:
                return s.episode_count
    except Exception:
        pass
    return None


def _resolve_ep_fresh(
    hls_template_sources: list, tmdb_api_key: str, source_name: str,
    title: str, year: int | None, tmdb_id: int | None,
    tvdb_id: int | None, season: int, ep_num: int,
) -> tuple[list, list[str]]:
    from backend.sources import build_sources
    from backend.domain.models import EpisodeWanted
    src = build_sources(hls_template_sources, tmdb_api_key=tmdb_api_key).get(source_name)
    if not src:
        return [], []
    wanted = EpisodeWanted(
        sonarr_episode_id=0, series_id=0, series_title=title, episode_title="",
        year=year, tmdb_id=tmdb_id, tvdb_id=tvdb_id, imdb_id=None,
        season_number=season, episode_number=ep_num,
    )
    hits = src.resolve_episode_all(wanted)
    return hits, list(getattr(src, "_last_log", []))


@router.post("/api/source-test")
async def source_test(request: Request) -> Response:
    try:
        params = await request.json()
    except Exception:
        return Response(status_code=400, content="Invalid JSON")

    settings = Settings.load()
    tmdb_id_raw = params.get("tmdb_id")
    tmdb_id = int(tmdb_id_raw) if tmdb_id_raw else None
    media_type = str(params.get("media_type", "movie"))
    season_raw = params.get("season")
    episode_raw = params.get("episode")
    tvdb_id_raw = params.get("tvdb_id")
    season: int | None = int(season_raw) if season_raw not in (None, "") else None
    episode: int | None = int(episode_raw) if episode_raw not in (None, "") else None
    tvdb_id: int | None = int(tvdb_id_raw) if tvdb_id_raw else None
    title = str(params.get("title") or "").strip()
    year_raw = params.get("year")
    year = int(year_raw) if year_raw else None

    # all_eps_mode: TV series + no specific episode → scan the full season
    # Works whether or not the user filled in the season field (defaults to S01)
    all_eps_mode = (media_type == "tv" and episode is None)
    eff_season = season if season is not None else 1
    eff_episode = episode if episode is not None else 1
    test_log: list[str] = [
        f"input: media_type={media_type}, tmdb_id={tmdb_id}, title={title!r}, "
        f"year={year}, season={season}, episode={episode}, tvdb_id={tvdb_id}",
    ]

    from backend.sources import build_sources
    from backend.adapters.tmdb import TmdbClient
    from backend.domain.models import MovieWanted, EpisodeWanted

    if tmdb_id and settings.tmdb_api_key:
        tmdb = TmdbClient(settings.tmdb_api_key)
        if media_type == "movie":
            info = tmdb.get_movie_info(tmdb_id)
            if info:
                title = title or info.title or ""
                year = year or info.series_year or None
                test_log.append(f"TMDB movie metadata: title={info.title!r}, year={info.series_year}")
            else:
                test_log.append("TMDB movie metadata lookup returned nothing")
        else:
            info = tmdb.get_series_info(tmdb_id)
            title = title or info.title or ""
            year = year or info.series_year or None
            test_log.append(
                f"TMDB series metadata: title={info.title!r}, year={info.series_year}, "
                f"seasons={info.total_seasons}, episodes={info.total_episodes}"
            )
    elif tmdb_id:
        test_log.append("TMDB API key not configured; add Title/Year manually")

    sources = build_sources(settings.hls_template_sources, tmdb_api_key=settings.tmdb_api_key)
    results: dict[str, dict] = {}

    if all_eps_mode:
        ep_count = _season_ep_count(tmdb_id, eff_season, settings)
        ep_count = min(ep_count or 13, 50)
        test_log.append(f"Scanning S{eff_season:02d}: {ep_count} episode(s)")
        for source_name in sources:
            ep_map: dict[int, list] = {}
            with ThreadPoolExecutor(max_workers=6) as pool:
                futs = {
                    pool.submit(
                        _resolve_ep_fresh,
                        settings.hls_template_sources, settings.tmdb_api_key,
                        source_name, title, year, tmdb_id, tvdb_id,
                        eff_season, ep_num,
                    ): ep_num
                    for ep_num in range(1, ep_count + 1)
                }
                for f in as_completed(futs):
                    ep_num = futs[f]
                    try:
                        hits, _ = f.result()
                        ep_map[ep_num] = hits
                    except Exception:
                        ep_map[ep_num] = []
            episodes_out = [
                {"num": n, "url": ep_map[n][0].hls_url if ep_map[n] else None}
                for n in sorted(ep_map)
            ]
            found = sum(1 for e in episodes_out if e["url"])
            results[source_name] = {
                "status": "ok" if found > 0 else "error",
                "message": None if found > 0 else "Not found",
                "episodes": episodes_out,
                "found": found,
                "total": ep_count,
                "log": test_log,
            }
    else:
        for source_name, source in sources.items():
            try:
                if media_type == "movie":
                    wanted: MovieWanted | EpisodeWanted = MovieWanted(
                        radarr_id=0, title=title, year=year, tmdb_id=tmdb_id, imdb_id=None
                    )
                    hits = source.resolve_movie_all(wanted)  # type: ignore[arg-type]
                else:
                    wanted = EpisodeWanted(
                        sonarr_episode_id=0, series_id=0, series_title=title, episode_title="",
                        year=year, tmdb_id=tmdb_id, tvdb_id=tvdb_id, imdb_id=None,
                        season_number=eff_season, episode_number=eff_episode,
                    )
                    hits = source.resolve_episode_all(wanted)  # type: ignore[arg-type]
                source_log = test_log + list(getattr(source, "_last_log", []))
                if hits:
                    urls = [{"url": h.hls_url, "server": h.server_name, "name": h.item_name} for h in hits]
                    results[source_name] = {"status": "ok", "url": hits[0].hls_url, "urls": urls, "log": source_log}
                else:
                    results[source_name] = {"status": "error", "message": "Not found", "log": source_log}
            except Exception as exc:
                source_log = test_log + list(getattr(source, "_last_log", [])) + [f"exception: {exc}"]
                results[source_name] = {"status": "error", "message": str(exc)[:200], "log": source_log}

    return JSONResponse(results)
