"""Tests for Jellyfin-compliant STRM output paths and TMDB title enrichment."""
from __future__ import annotations

from dataclasses import replace
from unittest.mock import MagicMock, patch

import pytest

from deceptarr.application.grab_service import _enrich_with_tmdb, _is_placeholder_title
from deceptarr.application.output_service import OutputService
from deceptarr.domain.models import GatewayJob, GatewayRelease
from deceptarr.infrastructure.config import Settings


# ── Placeholder title detection ───────────────────────────────────────────────

class TestIsPlaceholderTitle:
    def test_tmdb_id_is_placeholder(self):
        assert _is_placeholder_title("TMDB 24428") is True

    def test_tvdb_id_is_placeholder(self):
        assert _is_placeholder_title("TVDB 81189") is True

    def test_vn_source_is_placeholder(self):
        assert _is_placeholder_title("VN Source") is True

    def test_real_title_is_not_placeholder(self):
        assert _is_placeholder_title("The Avengers") is False
        assert _is_placeholder_title("Breaking Bad") is False
        assert _is_placeholder_title("Avengers: Endgame") is False


# ── TMDB title enrichment ─────────────────────────────────────────────────────

class TestEnrichWithTmdb:
    def _settings(self) -> Settings:
        return replace(Settings.load(), tmdb_api_key="fake-key")

    def test_enriches_movie_title_from_tmdb(self):
        release = GatewayRelease(
            title="TMDB 24428", kind="movie", output_mode="strm",
            source_name="kkphim", query="TMDB 24428", tmdb_id=24428,
        )
        with patch("deceptarr.application.grab_service.TmdbClient") as MockTmdb:
            client = MagicMock()
            client.enabled = True
            client.get_movie_title.return_value = ("The Avengers", 2012)
            MockTmdb.return_value = client

            enriched = _enrich_with_tmdb(self._settings(), release)

        assert enriched.title == "The Avengers"
        assert enriched.year == 2012
        assert enriched.tmdb_id == 24428  # unchanged

    def test_enriches_series_title_from_tmdb(self):
        from deceptarr.adapters.tmdb import TmdbSeriesInfo
        release = GatewayRelease(
            title="TVDB 81189", kind="episode", output_mode="strm",
            source_name="kkphim", query="", tmdb_id=1396,
            season_number=1, episode_number=1,
        )
        series_info = TmdbSeriesInfo(title="Breaking Bad", series_year=2008)
        with patch("deceptarr.application.grab_service.TmdbClient") as MockTmdb:
            client = MagicMock()
            client.enabled = True
            client.get_series_info.return_value = series_info
            MockTmdb.return_value = client

            enriched = _enrich_with_tmdb(self._settings(), release)

        assert enriched.title == "Breaking Bad"
        assert enriched.year == 2008

    def test_real_title_not_overwritten(self):
        release = GatewayRelease(
            title="Avengers: Endgame", kind="movie", output_mode="strm",
            source_name="kkphim", query="Avengers Endgame", tmdb_id=299534,
        )
        with patch("deceptarr.application.grab_service.TmdbClient") as MockTmdb:
            client = MagicMock()
            client.enabled = True
            MockTmdb.return_value = client

            enriched = _enrich_with_tmdb(self._settings(), release)

        # Should NOT call get_movie_title since title is not a placeholder
        client.get_movie_title.assert_not_called()
        assert enriched.title == "Avengers: Endgame"


# ── Jellyfin-compliant strm_path ──────────────────────────────────────────────

class TestStrmPath:
    def _settings(self, tmp_path) -> Settings:
        return replace(
            Settings.load(),
            movie_strm_root=str(tmp_path / "movies"),
            series_strm_root=str(tmp_path / "series"),
        )

    def _service(self, tmp_path) -> OutputService:
        return OutputService(self._settings(tmp_path))

    def _movie_job(self, title: str = "The Avengers", year: int = 2012) -> GatewayJob:
        release = GatewayRelease(
            title=title, kind="movie", output_mode="strm",
            source_name="kkphim", query=title, tmdb_id=24428, year=year,
        )
        return GatewayJob(job_id="abc", release=release, status="running",
                          progress=0.5, created_at=0, updated_at=0)

    def _episode_job(self, title: str = "Breaking Bad", season: int = 1, ep: int = 1) -> GatewayJob:
        release = GatewayRelease(
            title=title, kind="episode", output_mode="strm",
            source_name="kkphim", query=title, tvdb_id=81189, year=2008,
            season_number=season, episode_number=ep,
        )
        return GatewayJob(job_id="def", release=release, status="running",
                          progress=0.5, created_at=0, updated_at=0)

    def test_movie_path_jellyfin_format(self, tmp_path):
        svc = self._service(tmp_path)
        path = svc.strm_path(self._movie_job())
        # Jellyfin: movies/Title (Year)/Title (Year).strm
        assert path.endswith("The Avengers (2012)/The Avengers (2012).strm")

    def test_movie_path_no_year_omits_parens(self, tmp_path):
        svc = self._service(tmp_path)
        path = svc.strm_path(self._movie_job(year=0))
        assert "The Avengers" in path
        assert "(0)" not in path

    def test_episode_path_jellyfin_format(self, tmp_path):
        svc = self._service(tmp_path)
        path = svc.strm_path(self._episode_job(season=2, ep=5))
        # Jellyfin: series/Title/Season 02/Title - S02E05.strm
        assert "Breaking Bad" in path
        assert "Season 02" in path
        assert "Breaking Bad - S02E05.strm" in path
