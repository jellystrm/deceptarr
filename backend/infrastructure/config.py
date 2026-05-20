from __future__ import annotations

import json
import os
import shutil
import secrets
from dataclasses import dataclass, field
from typing import Any

import requests


# ─── Low-level helpers ────────────────────────────────────────────────────────


def _file_value(data: dict[str, Any], key: str, default: Any) -> Any:
    value = data.get(key)
    return default if value is None else value


def _value(data: dict[str, Any], key: str, env_name: str, default: Any) -> Any:
    """env var → config file → hardcoded default."""
    raw = os.getenv(env_name)
    if raw is not None and raw.strip() != "":
        return raw
    return _file_value(data, key, default)


def _int_value(data: dict[str, Any], key: str, env_name: str, default: int) -> int:
    raw = os.getenv(env_name)
    if raw is not None and raw.strip() != "":
        return int(raw)
    raw = _file_value(data, key, default)
    return int(raw)


def _bool_value(data: dict[str, Any], key: str, env_name: str, default: bool) -> bool:
    raw = os.getenv(env_name)
    if raw is not None:
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    return bool(_file_value(data, key, default))


def _list_file_value(data: dict[str, Any], key: str, default: list[str]) -> list[str]:
    """Read a list from config file only (no env override)."""
    raw = _file_value(data, key, default)
    if isinstance(raw, str):
        return [p.strip() for p in raw.split(",") if p.strip()]
    if isinstance(raw, list):
        return [str(p).strip() for p in raw if str(p).strip()]
    return list(default)


# ─── Constants ─────────────────────────────────────────────────────────────────

# ffmpeg binary candidates, checked in order
_FFMPEG_CANDIDATES: list[str] = ["ffmpeg", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]

# Default HLS download ffmpeg args — hardcoded defaults, adjustable via UI only
_FFMPEG_EXTRA_DEFAULTS: list[str] = [
    "-loglevel", "warning",
    "-stats",
]

# Candidate URLs probed when a service URL is not configured.
_SERVICE_CANDIDATES: dict[str, list[str]] = {
    "radarr": [
        "http://radarr:7878",
        "http://localhost:7878",
        "http://127.0.0.1:7878",
    ],
    "sonarr": [
        "http://sonarr:8989",
        "http://localhost:8989",
        "http://127.0.0.1:8989",
    ],
    "jellyfin": [
        "http://jellyfin:8096",
        "http://localhost:8096",
        "http://127.0.0.1:8096",
    ],
}

_SERVICE_ALIVE_PATH: dict[str, str] = {
    "radarr":   "/api/v3/system/status",
    "sonarr":   "/api/v3/system/status",
    "jellyfin": "/System/Info/Public",
}

_REQUEST_TIMEOUT: float = 1.5


# ─── ffmpeg auto-detection ────────────────────────────────────────────────────

def detect_ffmpeg() -> tuple[str, bool]:
    """Find the first available ffmpeg binary.

    Always searches in this order:
    1. ``FFMPEG_PATH`` environment variable
    2. ``ffmpeg`` on ``$PATH``
    3. ``/usr/bin/ffmpeg``
    4. ``/usr/local/bin/ffmpeg``

    Returns ``(path, found)``.
    """
    env_path = os.getenv("FFMPEG_PATH", "").strip()
    if env_path:
        if _ffmpeg_ok(env_path):
            return env_path, True

    for candidate in _FFMPEG_CANDIDATES:
        if _ffmpeg_ok(candidate):
            return candidate, True

    return env_path or "ffmpeg", False


def _ffmpeg_ok(path: str) -> bool:
    """True if *path* is executable ffmpeg."""
    return shutil.which(path) is not None


_FFMPEG_MISSING_HINT = (
    "ffmpeg not found on this system. Install it first:\n"
    "  macOS  → brew install ffmpeg\n"
    "  Debian/Ubuntu → apt-get install -y ffmpeg\n"
    "  Alpine      → apk add ffmpeg\n"
    "Then re-run deceptarr."
)


def ffmpeg_require(path: str) -> str:
    """Return *path* if ffmpeg is available, otherwise raise RuntimeError with install hint."""
    detected, found = detect_ffmpeg()
    resolved = path if path and shutil.which(path) else detected
    if not found:
        raise RuntimeError(_FFMPEG_MISSING_HINT)
    return resolved


# ─── Service URL auto-detection ────────────────────────────────────────────────

def _detect_service_url(service: str) -> str:
    """Return first reachable candidate URL for *service*, or ``""`` if none respond."""
    headers = {"Accept": "application/json"}
    for candidate in _SERVICE_CANDIDATES.get(service, []):
        try:
            path = _SERVICE_ALIVE_PATH.get(service, "/")
            resp = requests.get(f"{candidate}{path}", headers=headers, timeout=_REQUEST_TIMEOUT)
            if resp.status_code < 500:
                return candidate.rstrip("/")
        except Exception:
            pass
    return ""


def _detect_public_base_url(
    radarr_url: str,
    sonarr_url: str,
    jellyfin_url: str,
    ui_port: int,
) -> str:
    """Derive PUBLIC_BASE_URL from reachable service hostnames."""
    hosts: list[str] = []
    for svc_url in (radarr_url, sonarr_url, jellyfin_url):
        if svc_url:
            parsed = svc_url.replace("https://", "http://").split("/", 3)
            host_part = parsed[2] if len(parsed) > 2 else ""
            if host_part:
                hosts.append(host_part.split(":")[0])

    chosen: str = "127.0.0.1"
    for h in hosts:
        if h:
            chosen = h
            break
    return f"http://{chosen}:{ui_port}"


# ─── Arr path auto-detection ──────────────────────────────────────────────────

def _detect_arr_root_folder(service_url: str, api_key: str) -> str:
    """Return the first root folder path from Radarr or Sonarr, or ``""``."""
    if not service_url or not api_key:
        return ""
    try:
        resp = requests.get(
            f"{service_url.rstrip('/')}/api/v3/rootfolder",
            headers={"X-Api-Key": api_key, "Accept": "application/json"},
            timeout=3,
        )
        if resp.status_code == 200:
            folders = resp.json()
            if folders and isinstance(folders, list):
                path = folders[0].get("path", "")
                return path.rstrip("/") if path else ""
    except Exception:
        pass
    return ""


def _detect_download_root(service_url: str, api_key: str) -> str:
    """Query Radarr/Sonarr download client config and return the savePath, or ``""``."""
    if not service_url or not api_key:
        return ""
    try:
        resp = requests.get(
            f"{service_url.rstrip('/')}/api/v3/downloadclient",
            headers={"X-Api-Key": api_key, "Accept": "application/json"},
            timeout=3,
        )
        if resp.status_code == 200:
            clients = resp.json()
            if isinstance(clients, list):
                for client in clients:
                    for fld in client.get("fields", []):
                        if fld.get("name") == "savePath":
                            path = fld.get("value", "")
                            if path:
                                return str(path).rstrip("/")
    except Exception:
        pass
    return ""


# ─── TORZNAB_API_KEY lifecycle ─────────────────────────────────────────────────

def _generate_torznab_key() -> str:
    """Generate a persistent high-entropy Torznab API key."""
    return secrets.token_urlsafe(32)


# ─── Settings ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Settings:
    # ── Arr / Jellyfin ─────────────────────────────────────────────────────────
    radarr_url: str = ""
    radarr_api_key: str = ""
    sonarr_url: str = ""
    sonarr_api_key: str = ""
    jellyfin_url: str = ""
    jellyfin_api_key: str = ""

    # ── Storage ────────────────────────────────────────────────────────────────
    download_root: str = "/downloads"
    movie_strm_root: str = "/movies"
    series_strm_root: str = "/series"
    state_path: str = "appdata/deceptarr/state.json"
    config_path: str = "/config/config.json"

    # ── UI ─────────────────────────────────────────────────────────────────────
    ui_enabled: bool = True
    ui_host: str = "0.0.0.0"
    ui_port: int = 8765

    # ── Worker ─────────────────────────────────────────────────────────────────
    poll_interval_seconds: int = 300
    max_items_per_poll: int = 20
    retry_after_seconds: int = 86400
    run_once: bool = False
    worker_enabled: bool = True
    movie_enabled: bool = True
    series_enabled: bool = True

    # ── Output ─────────────────────────────────────────────────────────────────
    default_output_mode: str = "strm"
    expose_both_modes: bool = False
    download_container: str = "mkv"
    import_mode: str = "Move"

    # ── Auth ───────────────────────────────────────────────────────────────────
    torznab_api_key: str = ""
    public_base_url: str = ""
    qb_username: str = "admin"
    qb_password: str = "adminadmin"

    # ── External ───────────────────────────────────────────────────────────────
    tmdb_api_key: str = ""

    # ── ffmpeg ─────────────────────────────────────────────────────────────────
    ffmpeg_path: str = ""
    ffmpeg_extra_args: list[str] = field(default_factory=lambda: list(_FFMPEG_EXTRA_DEFAULTS))

    # ── Misc ───────────────────────────────────────────────────────────────────
    jellyfin_scan_after_strm: bool = False
    log_level: str = "INFO"
    job_detail_retention_hours: int = 24
    server_labels: list[str] = field(default_factory=lambda: ["ViệtSub", "Lồng Tiếng"])
    torznab_group_sources: bool = False
    hls_template_sources: list[dict[str, Any]] = field(default_factory=list)
    source_order: list[str] = field(default_factory=lambda: ["kkphim", "ophim", "nguonc"])

    def resolve_ffmpeg(self) -> str:
        """Return the ffmpeg binary path, auto-detecting if not yet resolved."""
        if self.ffmpeg_path and shutil.which(self.ffmpeg_path):
            return self.ffmpeg_path
        detected, found = detect_ffmpeg()
        if not found:
            raise RuntimeError(_FFMPEG_MISSING_HINT)
        return detected

    @staticmethod
    def load() -> "Settings":
        config_path = os.getenv("CONFIG_PATH", "").strip() or "/config/config.json"

        file_data: dict[str, Any] = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                file_data = loaded

        ui_port = _int_value(file_data, "ui_port", "UI_PORT", 8765)

        # ── API keys: file / UI only, no env override ─────────────────────────
        radarr_api_key  = str(_file_value(file_data, "radarr_api_key",  ""))
        sonarr_api_key  = str(_file_value(file_data, "sonarr_api_key",  ""))
        jellyfin_api_key = str(_file_value(file_data, "jellyfin_api_key", ""))
        tmdb_api_key    = str(_file_value(file_data, "tmdb_api_key",    ""))

        # ── Service URLs: config file → auto-probe network (persist if detected) ─
        _needs_persist = False

        radarr_url = str(_file_value(file_data, "radarr_url", "")).strip().rstrip("/")
        if not radarr_url:
            radarr_url = _detect_service_url("radarr")
            if radarr_url:
                _needs_persist = True
        sonarr_url = str(_file_value(file_data, "sonarr_url", "")).strip().rstrip("/")
        if not sonarr_url:
            sonarr_url = _detect_service_url("sonarr")
            if sonarr_url:
                _needs_persist = True
        jellyfin_url = str(_file_value(file_data, "jellyfin_url", "")).strip().rstrip("/")
        if not jellyfin_url:
            jellyfin_url = _detect_service_url("jellyfin")
            if jellyfin_url:
                _needs_persist = True

        # ── PUBLIC_BASE_URL: env → file → auto-detect ──────────────────────────
        raw_public = str(_value(file_data, "public_base_url", "PUBLIC_BASE_URL", "")).strip()
        if not raw_public:
            raw_public = _detect_public_base_url(radarr_url, sonarr_url, jellyfin_url, ui_port)

        # ── TORZNAB_API_KEY: env → file → auto-generate (persist if generated) ───
        raw_torznab_key = os.getenv("TORZNAB_API_KEY", "").strip()
        if not raw_torznab_key:
            raw_torznab_key = str(_file_value(file_data, "torznab_api_key", "")).strip()
        if not raw_torznab_key:
            raw_torznab_key = _generate_torznab_key()
            _needs_persist = True  # new key — save so it survives restarts

        # ── QB credentials: env (default admin/adminadmin) → file ─────────────
        qb_username = os.getenv("QB_USERNAME", "").strip()
        if not qb_username:
            qb_username = str(_file_value(file_data, "qb_username", "admin"))
        qb_password = os.getenv("QB_PASSWORD", "").strip()
        if not qb_password:
            qb_password = str(_file_value(file_data, "qb_password", "adminadmin"))

        # ── ffmpeg ─────────────────────────────────────────────────────────────
        file_ffmpeg_args = _file_value(file_data, "ffmpeg_extra_args", None)
        if file_ffmpeg_args is not None:
            if isinstance(file_ffmpeg_args, str):
                ffmpeg_extra_args = [a.strip() for a in file_ffmpeg_args.split(",") if a.strip()]
            else:
                ffmpeg_extra_args = [str(a) for a in file_ffmpeg_args]
        else:
            ffmpeg_extra_args = list(_FFMPEG_EXTRA_DEFAULTS)
        ffmpeg_path = str(_file_value(file_data, "ffmpeg_path", "")).strip()

        # ── hls_template_sources: file only, no env ────────────────────────────
        hls_template_sources = _file_value(file_data, "hls_template_sources", [])
        if not isinstance(hls_template_sources, list):
            hls_template_sources = []

        # ── source_order: file only ────────────────────────────────────────────
        source_order = _file_value(file_data, "source_order", ["kkphim", "ophim", "nguonc"])
        if not isinstance(source_order, list):
            source_order = ["kkphim", "ophim", "nguonc"]

        # ── Storage paths: config file → auto-detect from Arr → fallback ──────
        # Only detected (non-fallback) values are persisted; fallbacks are not
        # written so the next start retries detection when Arr becomes available.
        movie_strm_root = str(_file_value(file_data, "movie_strm_root", "")).strip()
        if not movie_strm_root:
            _detected = _detect_arr_root_folder(radarr_url, radarr_api_key)
            movie_strm_root = _detected or "/movies"
            if _detected:
                _needs_persist = True

        series_strm_root = str(_file_value(file_data, "series_strm_root", "")).strip()
        if not series_strm_root:
            _detected = _detect_arr_root_folder(sonarr_url, sonarr_api_key)
            series_strm_root = _detected or "/series"
            if _detected:
                _needs_persist = True

        download_root = str(_file_value(file_data, "download_root", "")).strip()
        if not download_root:
            _detected = (
                _detect_download_root(radarr_url, radarr_api_key)
                or _detect_download_root(sonarr_url, sonarr_api_key)
            )
            download_root = _detected or "/downloads"
            if _detected:
                _needs_persist = True

        settings = Settings(
            radarr_url=radarr_url,
            radarr_api_key=radarr_api_key,
            sonarr_url=sonarr_url,
            sonarr_api_key=sonarr_api_key,
            jellyfin_url=jellyfin_url,
            jellyfin_api_key=jellyfin_api_key,
            download_root=download_root,
            movie_strm_root=movie_strm_root,
            series_strm_root=series_strm_root,
            state_path=str(_file_value(file_data, "state_path", "appdata/deceptarr/state.json")),
            config_path=config_path,
            ui_enabled=_bool_value(file_data, "ui_enabled", "UI_ENABLED", True),
            ui_host=str(_value(file_data, "ui_host", "UI_HOST", "0.0.0.0")),
            ui_port=ui_port,
            poll_interval_seconds=_int_value(file_data, "poll_interval_seconds", "POLL_INTERVAL_SECONDS", 300),
            max_items_per_poll=_int_value(file_data, "max_items_per_poll", "MAX_ITEMS_PER_POLL", 20),
            retry_after_seconds=_int_value(file_data, "retry_after_seconds", "RETRY_AFTER_SECONDS", 86400),
            run_once=_bool_value(file_data, "run_once", "RUN_ONCE", False),
            worker_enabled=bool(_file_value(file_data, "worker_enabled", True)),
            movie_enabled=bool(_file_value(file_data, "movie_enabled", True)),
            series_enabled=bool(_file_value(file_data, "series_enabled", True)),
            default_output_mode=str(_file_value(file_data, "default_output_mode", "strm")),
            expose_both_modes=bool(_file_value(file_data, "expose_both_modes", False)),
            torznab_api_key=raw_torznab_key,
            public_base_url=raw_public,
            qb_username=qb_username,
            qb_password=qb_password,
            tmdb_api_key=tmdb_api_key,
            jellyfin_scan_after_strm=bool(_file_value(file_data, "jellyfin_scan_after_strm", False)),
            download_container=str(_file_value(file_data, "download_container", "mkv")),
            import_mode=str(_file_value(file_data, "import_mode", "Move")),
            ffmpeg_path=ffmpeg_path,
            ffmpeg_extra_args=ffmpeg_extra_args,
            log_level=str(_file_value(file_data, "log_level", "INFO")),
            job_detail_retention_hours=int(_file_value(file_data, "job_detail_retention_hours", 24)),
            server_labels=_list_file_value(file_data, "server_labels", ["ViệtSub", "Lồng Tiếng"]),
            torznab_group_sources=bool(_file_value(file_data, "torznab_group_sources", False)),
            hls_template_sources=hls_template_sources,  # type: ignore[arg-type]
            source_order=source_order,
        )

        # Persist any auto-detected / auto-generated values so the next start
        # reads them from file and skips the detection probes entirely.
        if _needs_persist:
            try:
                save_settings(settings.to_config_dict(), config_path)
            except Exception:
                pass  # non-fatal; detection will retry next restart

        return settings

    def to_config_dict(self) -> dict[str, Any]:
        return {
            "radarr_url": self.radarr_url,
            "radarr_api_key": self.radarr_api_key,
            "sonarr_url": self.sonarr_url,
            "sonarr_api_key": self.sonarr_api_key,
            "jellyfin_url": self.jellyfin_url,
            "jellyfin_api_key": self.jellyfin_api_key,
            "download_root": self.download_root,
            "movie_strm_root": self.movie_strm_root,
            "series_strm_root": self.series_strm_root,
            "state_path": self.state_path,
            "ui_enabled": self.ui_enabled,
            "ui_host": self.ui_host,
            "ui_port": self.ui_port,
            "poll_interval_seconds": self.poll_interval_seconds,
            "max_items_per_poll": self.max_items_per_poll,
            "retry_after_seconds": self.retry_after_seconds,
            "worker_enabled": self.worker_enabled,
            "movie_enabled": self.movie_enabled,
            "series_enabled": self.series_enabled,
            "default_output_mode": self.default_output_mode,
            "expose_both_modes": self.expose_both_modes,
            "torznab_api_key": self.torznab_api_key,
            "public_base_url": self.public_base_url,
            "qb_username": self.qb_username,
            "qb_password": self.qb_password,
            "tmdb_api_key": self.tmdb_api_key,
            "jellyfin_scan_after_strm": self.jellyfin_scan_after_strm,
            "download_container": self.download_container,
            "import_mode": self.import_mode,
            "ffmpeg_path": self.ffmpeg_path,
            "ffmpeg_extra_args": self.ffmpeg_extra_args,
            "log_level": self.log_level,
            "job_detail_retention_hours": self.job_detail_retention_hours,
            "server_labels": self.server_labels,
            "torznab_group_sources": self.torznab_group_sources,
            "hls_template_sources": self.hls_template_sources,
            "source_order": self.source_order,
        }


def save_settings(data: dict[str, Any], path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
    os.replace(tmp_path, path)
