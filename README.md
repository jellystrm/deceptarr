# Deceptarr

HLS source gateway for Radarr/Sonarr/Jellyseerr workflows.

It can run in two ways:

```text
Direct gateway mode:
Radarr/Sonarr -> Torznab indexer -> qBittorrent-compatible endpoint -> STRM or HLS download

Polling fallback mode:
Radarr/Sonarr wanted list -> worker poll -> HLS download -> Radarr/Sonarr import
```

The qBittorrent-compatible endpoint is only an API compatibility layer so Radarr/Sonarr can send grabs without patching their core. Internally this service either creates `.strm` files containing HLS URLs, or downloads HLS with `ffmpeg` to `.mkv`/`.mp4`.

Use this only with sources you are legally allowed to access and archive. Sources are configured via direct HLS templates or resolver endpoints you control; this service does not bypass DRM, login walls, token systems, or anti-bot protections.

## Quick Start

```bash
cp docker-compose.example.yml docker-compose.yml
docker compose up -d --build
```

Open:

```text
http://localhost:8765
```

## Add To Radarr/Sonarr

Add the indexer:

```text
Settings -> Indexers -> Add -> Torznab -> Custom

Name: Deceptarr
URL: http://deceptarr:8765/torznab/api
API Key: value from service UI, default deceptarr
Categories: 2000,2040,5000,5040
```

Add the download client:

```text
Settings -> Download Clients -> Add -> qBittorrent

Name: Deceptarr
Host: deceptarr
Port: 8765
Username: value from service UI, default admin
Password: value from service UI, default adminadmin
Category: deceptarr
```

The service implements the qBittorrent Web API endpoints Radarr/Sonarr commonly use for testing, adding, tracking, pausing/resuming, and deleting jobs:

```text
/api/v2/auth/login
/api/v2/app/version
/api/v2/app/webapiVersion
/api/v2/app/preferences
/api/v2/app/buildInfo
/api/v2/torrents/add
/api/v2/torrents/info
/api/v2/torrents/properties
/api/v2/torrents/files
/api/v2/torrents/delete
/api/v2/torrents/pause
/api/v2/torrents/resume
/api/v2/torrents/categories
/api/v2/sync/maindata
/api/v2/transfer/info
```

Manual search will show releases like:

```text
Movie 2026 1080p VN my-source [STRM]
Movie 2026 1080p VN my-source [HLS-DL]
```

`[STRM]` writes a `.strm` file. `[HLS-DL]` downloads the HLS stream with `ffmpeg`.

## Important Paths

For STRM mode:

```text
MOVIE_STRM_ROOT=/movies
SERIES_STRM_ROOT=/shows
```

These should be Jellyfin library paths.

For HLS download mode:

```text
DOWNLOAD_ROOT=/downloads/vn
```

This path should be visible to Radarr/Sonarr if you want them to import completed downloads.

## Supported Sources

Template/resolver based:

```text
vidsrc
embed
any custom name
```

Example direct HLS template:

```json
[
  {
    "name": "embed",
    "movie_url_template": "https://resolver.example/movie/{tmdb_id}.m3u8",
    "series_url_template": "https://resolver.example/tv/{tvdb_id}/s{season:02d}e{episode:02d}.m3u8",
    "headers": {
      "Referer": "https://resolver.example/"
    }
  }
]
```

Example resolver endpoint:

```json
[
  {
    "name": "vidsrc",
    "movie_resolver_url_template": "http://my-resolver:7000/movie/{tmdb_id}",
    "series_resolver_url_template": "http://my-resolver:7000/tv/{tvdb_id}/{season}/{episode}"
  }
]
```

Resolver endpoints can return plain text containing a `.m3u8` URL, or JSON:

```json
{
  "hls_url": "https://example/master.m3u8",
  "headers": {
    "Referer": "https://example/"
  }
}
```

Available template fields:

```text
title, year, tmdb_id, tvdb_id, imdb_id, season, episode
```

## Local Smoke Test

```bash
cd deceptarr
python3 -m deceptarr --once
```

Full gateway smoke test:

```bash
./scripts/smoke-test.sh
```

Start the UI locally:

```bash
./run
```

## Environment

Most settings are auto-detected and do not require configuration:

| Variable | Default | Notes |
|---|---:|---|
| `UI_PORT` | `8765` | UI listen port |
| `TMDB_API_KEY` | empty | Required for TV resolution via Torznab (TVDB → TMDB lookup). Get free at themoviedb.org |
| `LOG_LEVEL` | `INFO` | Python logging level |

### Auto-detected values (no config needed)

- **Jellyfin/Radarr/Sonarr URLs**: Auto-probed from `http://jellyfin:8096`, `http://radarr:7878`, `http://sonarr:8989`, `localhost`, and `127.0.0.1`
- **TORZNAB_API_KEY**: Auto-generated persistent random key (stored in config file)
- **DOWNLOAD_ROOT**: Uses `/downloads` by default; in Docker, follows the mounted download folder
- **CONFIG_PATH**: Fixed at `/config/config.json`
- **STATE_PATH**: Fixed at `/config/state.json`
- **FFMPEG_PATH**: Auto-detected (`ffmpeg` on PATH, `/usr/bin/ffmpeg`, or `/usr/local/bin/ffmpeg`). Raises error if not found.
- **FFMPEG_EXTRA_ARGS**: Uses sensible defaults (`-loglevel warning -stats`), adjustable via UI

### UI-configurable settings

The following can be configured via the web UI (saved to `/config/config.json`):

- Radarr/Sonarr API keys
- Jellyfin URL and API key
- Download paths (movies, series, downloads)
- Output mode (strm vs download)
- Torznab API key (with regenerate button)
- FFMPEG extra arguments
- Worker settings (poll interval, etc.)
- Source templates
