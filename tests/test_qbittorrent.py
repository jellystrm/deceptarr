"""Tests for qBittorrent-compat job control — pause/resume(retry)/delete."""
from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import pytest
from vn_source_gateway.domain.models import GatewayJob, GatewayRelease
from vn_source_gateway.infrastructure.config import Settings
from vn_source_gateway.infrastructure.jobs import JobStore
from vn_source_gateway.interfaces.download_clients import qbittorrent


@pytest.fixture
def settings(tmp_path) -> Settings:
    return replace(Settings.load(), state_path=str(tmp_path / "state.json"))


def _release() -> GatewayRelease:
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
