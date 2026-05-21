from __future__ import annotations

from .base import Source
from .nguonc import NguonCSource
from .phimapi import PhimApiSource

__all__ = [
    "Source",
    "PhimApiSource",
    "NguonCSource",
    "build_sources",
    "BUILTIN_SOURCES",
]

# API documentation:
#   kkphim  https://kkphim.vip/tai-lieu-api        (PhimAPI-compatible)
#   ophim   https://ophim17.cc/api-document         (PhimAPI-compatible docs)
#   nguonc  https://phim.nguonc.com/api-document    (custom schema)
BUILTIN_SOURCES: dict[str, str] = {
    "kkphim": "https://phimapi.com",
    "ophim": "https://ophim1.com",
    "nguonc": "https://phim.nguonc.com",
}

# Default source priority order (used when source_order is empty in config)
DEFAULT_SOURCE_ORDER: list[str] = ["kkphim", "ophim", "nguonc"]


def build_sources(tmdb_api_key: str = "") -> dict[str, Source]:
    """Build the built-in source registry."""
    return {
        "kkphim": PhimApiSource("kkphim", BUILTIN_SOURCES["kkphim"], tmdb_api_key=tmdb_api_key),
        "ophim": PhimApiSource("ophim", BUILTIN_SOURCES["ophim"], tmdb_api_key=tmdb_api_key),
        "nguonc": NguonCSource("nguonc", BUILTIN_SOURCES["nguonc"], tmdb_api_key=tmdb_api_key),
    }
