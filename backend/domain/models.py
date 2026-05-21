from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class MovieWanted:
    radarr_id: int
    title: str
    year: int | None
    tmdb_id: int | None
    imdb_id: str | None
    server_label: str = ""

    @property
    def key(self) -> str:
        return f"movie:{self.tmdb_id or self.radarr_id}"


@dataclass(frozen=True)
class EpisodeWanted:
    sonarr_episode_id: int
    series_id: int
    series_title: str
    episode_title: str
    year: int | None
    tmdb_id: int | None
    tvdb_id: int | None
    imdb_id: str | None
    season_number: int
    episode_number: int
    server_label: str = ""

    @property
    def key(self) -> str:
        return f"episode:{self.tvdb_id or self.series_id}:s{self.season_number:02d}e{self.episode_number:02d}"


@dataclass(frozen=True)
class SourceHit:
    source_name: str
    hls_url: str
    headers: dict[str, str]
    server_name: str = ""
    item_name: str = ""
    raw_data: dict | None = None


OutputMode = Literal["strm", "download"]
MediaKind = Literal["movie", "episode"]


@dataclass(frozen=True)
class GatewayRelease:
    title: str
    kind: MediaKind
    output_mode: OutputMode
    source_name: str | None
    query: str
    year: int | None = None
    tmdb_id: int | None = None
    imdb_id: str | None = None
    tvdb_id: int | None = None
    season_number: int | None = None
    episode_number: int | None = None
    server_label: str = ""
    container: str | None = None  # per-job container override (mkv/mp4); None = use global default


@dataclass(frozen=True)
class GatewayJob:
    job_id: str
    release: GatewayRelease
    status: str
    progress: float
    created_at: int
    updated_at: int
    category: str = "deceptarr"
    paused: bool = False
    save_path: str | None = None
    hls_url: str | None = None
    error: str | None = None
    search_log: list[str] = field(default_factory=list)
    source_raw: dict | None = None
