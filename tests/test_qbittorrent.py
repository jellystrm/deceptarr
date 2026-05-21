"""Tests for qBittorrent-compat job control — pause/resume(retry)/delete."""
from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import pytest
from backend.domain.models import GatewayJob, GatewayRelease
from backend.infrastructure.config import Settings
from backend.infrastructure.jobs import JobStore
from backend.interfaces.download_clients import qbittorrent


@pytest.fixture
def settings(tmp_path) -> Settings:
    return replace(Settings.load(), state_path=str(tmp_path / "state.json"))


def _release(kind: str = "movie") -> GatewayRelease:
    if kind == "episode":
        return GatewayRelease(
            title="Breaking Bad", kind="episode", output_mode="strm",
            source_name="kkphim", query="Breaking Bad", tvdb_id=81189,
            season_number=1, episode_number=1,
        )
    return GatewayRelease(
        title="Avengers", kind="movie", output_mode="strm",
        source_name="kkphim", query="Avengers", tmdb_id=24428,
    )


def _seed(settings: Settings, status: str, paused: bool = False) -> str:
    store = JobStore(settings.state_path)
    job = GatewayJob(
        job_id="job123", release=_release(), status=status,
        progress=0.0, created_at=1, updated_at=1, paused=paused,
    )
    store.upsert(job)
    return job.job_id


class TestDelete:
    def test_delete_marks_deleted_and_hides_from_info(self, settings):
        _seed(settings, "completed")
        qbittorrent.delete(settings, "job123")
        assert JobStore(settings.state_path).get("job123").status == "deleted"
        assert qbittorrent.torrents_info(settings) == []


class TestTorrentInfo:
    def test_generic_movie_category_is_reported_as_radarr(self, settings):
        _seed(settings, "queued")
        [item] = qbittorrent.torrents_info(settings)
        assert item["category"] == "radarr"

    def test_category_filter_separates_radarr_and_sonarr(self, settings):
        store = JobStore(settings.state_path)
        store.upsert(
            GatewayJob(
                job_id="movie-job", release=_release("movie"), status="queued",
                progress=0.0, created_at=1, updated_at=1, category="deceptarr",
            )
        )
        store.upsert(
            GatewayJob(
                job_id="episode-job", release=_release("episode"), status="queued",
                progress=0.0, created_at=1, updated_at=1, category="deceptarr",
            )
        )

        radarr = qbittorrent.torrents_info(settings, category="radarr")
        sonarr = qbittorrent.torrents_info(settings, category="sonarr")

        assert [item["hash"] for item in radarr] == ["movie-job"]
        assert [item["hash"] for item in sonarr] == ["episode-job"]


class TestPause:
    def test_pause_sets_flag(self, settings):
        _seed(settings, "running")
        qbittorrent.pause(settings, "job123", True)
        assert JobStore(settings.state_path).get("job123").paused is True


class TestResumeIsRetry:
    """Regression: Resume on error/running/queued must re-run process_job.
    Previously only status=='queued' restarted, so failed jobs were dead."""

    @pytest.mark.parametrize("status", ["error", "running", "queued"])
    def test_resume_requeues_and_spawns(self, settings, status):
        _seed(settings, status, paused=False)
        with patch.object(qbittorrent.threading, "Thread") as mock_thread:
            qbittorrent.pause(settings, "job123", False)
        job = JobStore(settings.state_path).get("job123")
        assert job.status == "queued"
        assert job.error is None
        assert job.paused is False
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()

    def test_resume_completed_does_not_respawn(self, settings):
        _seed(settings, "completed", paused=False)
        with patch.object(qbittorrent.threading, "Thread") as mock_thread:
            qbittorrent.pause(settings, "job123", False)
        job = JobStore(settings.state_path).get("job123")
        assert job.status == "completed"  # not re-queued
        assert job.paused is False
        mock_thread.assert_not_called()

    def test_resume_missing_job_is_noop(self, settings):
        with patch.object(qbittorrent.threading, "Thread") as mock_thread:
            qbittorrent.pause(settings, "nope", False)
        mock_thread.assert_not_called()
