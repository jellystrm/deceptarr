"""Settings tab — tabbed settings panel for all configuration sections."""
from __future__ import annotations

import html
from typing import Any

from .cards import (
    _attr,
    radarr_card, sonarr_card, worker_card, tasks_card,
    output_card, indexer_card, downloader_card, jellyfin_card,
)

_TABS = [
    ("radarr",      "Radarr"),
    ("sonarr",      "Sonarr"),
    ("worker",      "Worker"),
    ("tasks",       "Tasks"),
    ("output",      "Output"),
    ("indexer",     "Indexer"),
    ("downloader",  "Download Client"),
    ("jellyfin",    "Jellyfin"),
]
_VALID_TABS = {key for key, _ in _TABS}


def _form(section: str, card_html: str, extra_btn: str = "") -> str:
    return (
        f'<form method="post" action="/save">'
        f'<input type="hidden" name="_section" value="{html.escape(section)}">'
        f"{card_html}"
        f'<div class="actions">'
        f'<button type="submit" class="btn btn-primary">&#10003; Save</button>'
        f"{extra_btn}"
        f"</div></form>"
    )


def settings_panel(config: dict[str, Any], ffmpeg_args: str, active_tab: str) -> str:
    active = active_tab if active_tab in _VALID_TABS else "radarr"

    tab_html = "\n      ".join(
        f'<a href="/?tab=settings&stab={_attr(key)}" '
        f'class="settings-tab{" active" if key == active else ""}">'
        f"{html.escape(label)}</a>"
        for key, label in _TABS
    )

    test_btn = lambda name: (
        f'<button type="submit" formaction="/test" class="btn btn-ghost">Test {html.escape(name)}</button>'
    )

    form_map = {
        "radarr":     _form("radarr",     radarr_card(config),             test_btn("Radarr")),
        "sonarr":     _form("sonarr",     sonarr_card(config),             test_btn("Sonarr")),
        "worker":     _form("worker",     worker_card(config)),
        "tasks":      _form("tasks",      tasks_card(config)),
        "output":     _form("runtime",    output_card(config, ffmpeg_args)),
        "indexer":    _form("indexer",    indexer_card(config)),
        "downloader": _form("downloader", downloader_card(config)),
        "jellyfin":   _form("jellyfin",   jellyfin_card(config)),
    }

    return f"""
    <div class="settings-tabs" role="tablist">
      {tab_html}
    </div>
    {form_map[active]}"""
