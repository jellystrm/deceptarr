from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.api import create_app
from backend.domain.models import GatewayJob, GatewayRelease
from backend.infrastructure.activity import ActivityLog
from backend.infrastructure.jobs import JobStore


def test_health_uses_ophim_home_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path / "config.json"))
    client = TestClient(create_app())
    response = MagicMock()
    response.status_code = 200

    with patch("requests.get", return_value=response) as mock_get:
        result = client.get("/api/health")

    assert result.status_code == 200
    assert result.json()["ophim"]["url"] == "https://ophim1.com/v1/api/home"
    called_urls = [call.args[0] for call in mock_get.call_args_list]
    assert "https://ophim1.com/v1/api/home" in called_urls


def test_test_grabber_adds_linkgrabber_activity(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path / "config.json"))
    ActivityLog.init(str(tmp_path / "activity.json"))
    client = TestClient(create_app())

    response = client.post(
        "/api/test-grabber",
        json={"media_type": "tv", "tmdb_id": 37854, "title": "One Piece", "year": 1999},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["count"] > 0

    events = client.get("/api/activity").json()
    assert events[0]["kind"] == "search"
    assert events[0]["title"] == "TV: One Piece"
    assert events[0]["grabs"]
    assert events[0]["grabs"][0]["media_kind"] == "episode"
    assert events[0]["grabs"][0]["media_title"] == "One Piece"
    assert events[0]["grabs"][0]["season"] is None
    assert events[0]["grabs"][0]["episode"] is None


def test_test_indexer_returns_torznab_items(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path / "config.json"))
    ActivityLog.init(str(tmp_path / "activity.json"))
    client = TestClient(create_app())

    response = client.post(
        "/api/test-indexer",
        json={"media_type": "movie", "tmdb_id": 27205, "title": "Inception", "year": 2010},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["count"] > 0
    assert body["key_required"] is True
    assert "apikey=***" in body["url"]
    assert any("Inception" in title for title in body["results"])


def test_activity_delete_removes_event(tmp_path, monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path / "config.json"))
    ActivityLog.init(str(tmp_path / "activity.json"))
    client = TestClient(create_app())
    ActivityLog.get().add("search", "Movie: Test", grabs=[{"title": "Test", "token": "abc"}])
    event = client.get("/api/activity").json()[0]

    response = client.post("/api/activity/delete", json={"ts": event["ts"], "title": event["title"]})

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert client.get("/api/activity").json() == []


def test_pipeline_enriches_placeholder_job_title(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    state_path = tmp_path / "state.json"
    config_path.write_text(
        json.dumps({"state_path": str(state_path), "tmdb_api_key": "fake-key"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CONFIG_PATH", str(config_path))
    monkeypatch.setenv("TMDB_API_KEY", "fake-key")
    store = JobStore(str(state_path))
    store.upsert(
        GatewayJob(
            job_id="movie:24428",
            release=GatewayRelease(
                title="TMDB 24428",
                kind="movie",
                output_mode="strm",
                source_name=None,
                query="TMDB 24428",
                tmdb_id=24428,
            ),
            status="queued",
            progress=0,
            created_at=1,
            updated_at=1,
        )
    )
    client = TestClient(create_app())

    with patch("backend.application.grab_service.TmdbClient") as mock_tmdb:
        tmdb = MagicMock()
        tmdb.enabled = True
        tmdb.get_movie_title.return_value = ("The Avengers", 2012)
        mock_tmdb.return_value = tmdb
        response = client.get("/api/pipeline")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "The Avengers"
