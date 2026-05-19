from __future__ import annotations

import logging
import threading
from typing import Any

import requests

log = logging.getLogger(__name__)

_BASE = "https://api.tvmaze.com"

# Process-lifetime cache — TVMaze IDs and episode lists are stable.
_cache: dict[str, Any] = {}
_lock = threading.Lock()


class TVMazeClient:
    """Thin TVMaze client for TVDB-aligned season/episode lookups.

    TVMaze is free (no API key), and its episode numbering mirrors TVDB,
    making it the correct source when Sonarr/TVDB season numbers are needed.
    """

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    # ── Public API ────────────────────────────────────────────────────────────

    def get_season_episodes(self, tvdb_id: int, season: int) -> list[int]:
        """Return ordered episode numbers for *season* of a show identified by *tvdb_id*.

        Uses TVDB-aligned numbering (i.e. the same numbers Sonarr sends).
        Returns an empty list on any error or miss.
        """
        cache_key = f"tvmaze:season_eps:{tvdb_id}:{season}"
        with _lock:
            if cache_key in _cache:
                return _cache[cache_key]
        result = self._fetch_season_episodes(tvdb_id, season)
        with _lock:
            _cache[cache_key] = result
        return result

    # ── Internal ─────────────────────────────────────────────────────────────

    def _get_show_id(self, tvdb_id: int) -> int | None:
        cache_key = f"tvmaze:show:{tvdb_id}"
        with _lock:
            if cache_key in _cache:
                return _cache[cache_key]
        result = self._fetch_show_id(tvdb_id)
        with _lock:
            _cache[cache_key] = result
        return result

    def _fetch_show_id(self, tvdb_id: int) -> int | None:
        try:
            r = self.session.get(
                f"{_BASE}/lookup/shows",
                params={"thetvdb": tvdb_id},
                timeout=10,
            )
            if r.status_code != 200:
                return None
            data = r.json()
            return int(data["id"])
        except Exception as exc:
            log.debug("TVMaze show lookup failed for tvdb_id=%s: %s", tvdb_id, exc)
            return None

    def _fetch_season_episodes(self, tvdb_id: int, season: int) -> list[int]:
        show_id = self._get_show_id(tvdb_id)
        if not show_id:
            return []
        try:
            r = self.session.get(
                f"{_BASE}/shows/{show_id}/episodes",
                timeout=10,
            )
            if r.status_code != 200:
                return []
            episodes: list[dict[str, Any]] = r.json()
            return sorted(
                e["number"]
                for e in episodes
                if e.get("season") == season and e.get("number")
            )
        except Exception as exc:
            log.debug("TVMaze episodes failed for show=%s season=%s: %s", show_id, season, exc)
            return []
