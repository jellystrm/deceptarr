from __future__ import annotations

from typing import Any

from .base import Source
from .template import DirectHlsTemplateSource

__all__ = ["Source", "DirectHlsTemplateSource", "build_sources"]


def build_sources(template_configs: list[dict[str, Any]], tmdb_api_key: str = "") -> dict[str, Source]:
    sources: dict[str, Source] = {}
    for config in template_configs:
        source = DirectHlsTemplateSource(config)
        sources[source.name] = source
    return sources
