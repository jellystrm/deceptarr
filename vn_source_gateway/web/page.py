from __future__ import annotations

import html
import json

from vn_source_gateway.infrastructure.config import Settings
from vn_source_gateway.interfaces.download_clients import qbittorrent
from .cards import (
    _attr,
    download_tasks_card,
    settings_card,
    sources_card,
)
from .styles import CSS

_NAV = [
    ("dashboard", "Dashboard"),
    ("sources", "Sources"),
    ("settings", "Settings"),
]

SECTION_ALIASES = {
    "download-tasks": "dashboard",
    "jobs": "dashboard",
    "media-managers": "settings",
    "radarr": "settings",
    "sonarr": "settings",
    "worker": "settings",
    "indexer": "settings",
    "downloader": "settings",
    "jellyfin": "settings",
}
ALL_SECTIONS = {s for s, _ in _NAV} | set(SECTION_ALIASES)


def render_page(settings: Settings, message: str, section: str, settings_tab: str = "") -> str:
    requested_section = section
    section = SECTION_ALIASES.get(section, section)
    if section == "settings" and not settings_tab:
        settings_tab = {
            "media-managers": "radarr",
            "radarr": "radarr",
            "sonarr": "sonarr",
            "worker": "worker",
            "indexer": "indexer",
            "downloader": "downloader",
            "jellyfin": "jellyfin",
        }.get(requested_section, "")
    config = settings.to_config_dict()
    templates = json.dumps(config["hls_template_sources"], indent=2)
    source_order = ",".join(config["source_order"])
    ffmpeg_args = ",".join(config["ffmpeg_extra_args"])
    msg_html = f'<div class="notice">{html.escape(message)}</div>' if message else ""
    section_title = {
        "dashboard": "Dashboard",
        "sources": "Sources",
        "settings": "Settings",
    }.get(section, "Dashboard")

    card_html, has_form = _section_card(section, settings, config, templates, source_order, ffmpeg_args, settings_tab)

    if has_form:
        test_button = ""
        if section in {"radarr", "sonarr"}:
            label = "Test Radarr" if section == "radarr" else "Test Sonarr"
            test_button = f'\n      <button type="submit" formaction="/test" class="btn btn-ghost">{label}</button>'
        actions = """
    <div class="actions">
      <button type="submit" class="btn btn-primary">&#10003; Save Changes</button>""" + test_button + """
    </div>"""
        content = f"""
  <form method="post" action="/save">
    <input type="hidden" name="_section" value="{html.escape(section)}">
    {card_html}
    {actions}
  </form>"""
    else:
        content = card_html

    nav_items = "\n".join(
        f'    <a href="/{s}" class="nav-item{"  active" if s == section else ""}">{label}</a>'
        for s, label in _NAV
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  {'<meta http-equiv="refresh" content="5">' if section == "dashboard" else ""}
  <title>vn-source-gateway</title>
  <style>{CSS}</style>
</head>
<body>

<nav class="sidebar">
  <a class="sidebar-brand" href="/dashboard">
    <div class="brand-icon">V</div>
    <div>
      <div class="brand-name">vn-source-gateway</div>
      <div class="brand-sub">Media Source Gateway</div>
    </div>
  </a>
  <div class="nav-group">
{nav_items}
  </div>
</nav>

<div class="topbar">
  <span class="topbar-title">{section_title} <span class="topbar-sub">{_attr(settings.config_path)}</span></span>
</div>

<main class="main">
  {msg_html}

  {content}

</main>

</body>
</html>"""


def _section_card(
    section: str,
    settings: Settings,
    config: dict,
    templates: str,
    source_order: str,
    ffmpeg_args: str,
    settings_tab: str,
) -> tuple[str, bool]:
    if section == "dashboard":
        return download_tasks_card(_tasks_html(settings)), False
    if section == "sources":
        return sources_card(config, templates, source_order), True
    if section == "settings":
        return settings_card(config, ffmpeg_args, settings_tab), False
    return download_tasks_card(_tasks_html(settings)), False


def _tasks_html(settings: Settings) -> str:
    try:
        jobs = qbittorrent.torrents_info(settings)
    except Exception as exc:
        return f"<p style='color:var(--muted)'>Could not load jobs: {html.escape(str(exc))}</p>"
    if not jobs:
        return "<p style='color:var(--muted);font-size:13px'>No download tasks yet.</p>"
    rows = []
    for job in sorted(jobs, key=lambda item: item.get("added_on", 0), reverse=True)[:25]:
        state = str(job.get("state", ""))
        if state in {"uploading", "pausedUP"}:
            badge_cls, label, bar_cls = "completed", "completed", "done"
        elif "error" in state.lower():
            badge_cls, label, bar_cls = "error", "failed", "fail"
        elif state == "downloading":
            badge_cls, label, bar_cls = "running", "downloading", ""
        elif state == "pausedDL":
            badge_cls, label, bar_cls = "", "paused", ""
        else:
            badge_cls, label, bar_cls = "", "queued", ""
        progress = int(float(job.get("progress", 0)) * 100)
        task_hash = _attr(job.get("hash", ""))

        # Context-aware actions
        buttons = ""
        if state == "error":
            buttons += "<button type='submit' name='action' value='resume' class='btn btn-ghost btn-small'>Retry</button>"
        elif state in {"downloading", "queuedDL"}:
            buttons += "<button type='submit' name='action' value='pause' class='btn btn-ghost btn-small'>Pause</button>"
        elif state == "pausedDL":
            buttons += "<button type='submit' name='action' value='resume' class='btn btn-ghost btn-small'>Resume</button>"
        buttons += "<button type='submit' name='action' value='delete' class='btn btn-danger btn-small'>Delete</button>"

        rows.append(
            "<tr>"
            f"<td>{html.escape(str(job.get('name', '')))}</td>"
            f"<td><span class='badge {badge_cls}'>{label}</span></td>"
            f"<td><div class='pbar'><span class='pbar-fill {bar_cls}' style='width:{progress}%'></span>"
            f"<span class='pbar-txt'>{progress}%</span></div></td>"
            f"<td style='color:var(--muted)'>{html.escape(str(job.get('save_path', '')) or '—')}</td>"
            "<td>"
            f"<form method='post' action='/tasks/action' class='task-actions'>"
            f"<input type='hidden' name='hashes' value='{task_hash}'>"
            f"{buttons}"
            "</form>"
            "</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Name</th><th>State</th><th>Progress</th><th>Path</th><th>Actions</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )
