from __future__ import annotations

import html
import json

from vn_source_gateway.infrastructure.config import Settings
from vn_source_gateway.interfaces.download_clients import qbittorrent
from .cards import (
    _attr,
    activity_log_card,
    download_tasks_card,
    settings_card,
    sources_card,
)
from .styles import CSS

# ---------------------------------------------------------------------------
# Dashboard live-update script
# Polls /dashboard every 5 s and replaces just the #pipeline card in-place,
# preserving the open/closed state of every <details> panel so the user
# doesn't lose their expanded rows on refresh.
# ---------------------------------------------------------------------------
_DASHBOARD_POLL_JS = r"""
(function () {
  var INTERVAL = 5000;

  function openKeys() {
    var keys = new Set();
    document.querySelectorAll('#pipeline details[open]').forEach(function (d) {
      var td = d.closest('td');
      if (td) keys.add(td.textContent.trim().slice(0, 80));
    });
    return keys;
  }
  function restoreOpen(keys) {
    document.querySelectorAll('#pipeline details').forEach(function (d) {
      var td = d.closest('td');
      if (td && keys.has(td.textContent.trim().slice(0, 80))) d.open = true;
    });
  }

  function activeTab() {
    var a = document.querySelector('#pipeline .jd-tab.active');
    return a ? a.dataset.tab : 'downloads';
  }

  window.jdSwitchTab = function(tab) {
    document.querySelectorAll('#pipeline .jd-tab').forEach(function(t) {
      t.classList.toggle('active', t.dataset.tab === tab);
    });
    document.querySelectorAll('#pipeline .jd-pane').forEach(function(p) {
      p.style.display = (p.id === 'jd-' + tab) ? '' : 'none';
    });
    document.querySelectorAll('#pipeline .jd-statusbar').forEach(function(s) {
      s.style.display = (s.id === 'jd-sb-' + tab) ? '' : 'none';
    });
  };

  function refresh() {
    var open = openKeys();
    var tab = activeTab();
    fetch('/dashboard', {cache: 'no-store'})
      .then(function (r) { return r.text(); })
      .then(function (text) {
        var tmp = document.createElement('div');
        tmp.innerHTML = text;
        var newCard = tmp.querySelector('#pipeline');
        var oldCard = document.getElementById('pipeline');
        if (newCard && oldCard) {
          oldCard.replaceWith(newCard);
          window.jdSwitchTab(tab);
          restoreOpen(open);
        }
      })
      .catch(function () {});
  }

  setInterval(refresh, INTERVAL);
  refresh(); // scan immediately on page load

  // Intercept task-action and manual-grab form submits via fetch
  document.addEventListener('submit', function (e) {
    if (!e.target.classList.contains('task-actions')) return;
    e.preventDefault();
    fetch(e.target.action, {method: 'POST', body: new FormData(e.target)})
      .catch(function () {})
      .finally(function () { refresh(); });
  });

  // Bulk toolbar actions (Start All / Pause All / Clear Done)
  window.jdBulkAction = function(action) {
    fetch('/tasks/bulk', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'action=' + encodeURIComponent(action)
    }).catch(function(){}).finally(function() { refresh(); });
  };
})();
"""

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
    "tasks": "settings",
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
            "tasks": "tasks",
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

<main class="main{' dashboard' if section == 'dashboard' else ' constrained'}">
  {msg_html}

  {content}

</main>

{'<script>' + _DASHBOARD_POLL_JS + '</script>' if section == "dashboard" else ""}
{"<script>document.addEventListener('DOMContentLoaded',function(){var a=document.activeElement;if(a&&(a.tagName==='INPUT'||a.tagName==='TEXTAREA'||a.tagName==='SELECT'))a.blur();});</script>" if section == "settings" else ""}
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
        return _pipeline_card(settings), False
    if section == "sources":
        return sources_card(config, templates, source_order), False  # manages its own form
    if section == "settings":
        return settings_card(config, ffmpeg_args, settings_tab), False
    return _pipeline_card(settings), False


def _detail_panel(steps: list[tuple[str, str, str, str]], open_by_default: bool = True) -> str:
    """Build a collapsible <details> panel showing pipeline step details.

    steps: list of (icon, name, message, status)  — status is "ok" | "error" | ""
    """
    rows_html = ""
    for icon, name, msg, status in steps:
        if not msg:
            continue
        msg_class = "pipe-step-msg"
        if status == "ok":
            msg_class += " ok"
        elif status == "error":
            msg_class += " err"
        rows_html += (
            f"<div class='pipe-step'>"
            f"<span class='pipe-step-icon'>{icon}</span>"
            f"<span class='pipe-step-name'>{html.escape(name)}</span>"
            f"<span class='{msg_class}'>{html.escape(msg)}</span>"
            f"</div>"
        )
    if not rows_html:
        return ""
    open_attr = " open" if open_by_default else ""
    return (
        f"<details class='pipe-detail'{open_attr}>"
        f"<summary>details</summary>"
        f"<div class='pipe-steps'>{rows_html}</div>"
        f"</details>"
    )


def _time_ago(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def _pipeline_card(settings: Settings) -> str:
    """JDownloader-style tabbed layout: LinkGrabber + Downloads tabs."""
    lg_html, lg_pkgs, lg_links, lg_errors = _indexer_card(settings)
    dl_html, dl_pkgs, dl_running, dl_errors = _download_card(settings)

    lg_statusbar = (
        f"<div class='jd-sb-row'>"
        f"<span class='jd-stat'><span class='jd-stat-label'>Package(s):</span>"
        f"<span class='jd-stat-val'>{lg_pkgs}</span></span>"
        f"<span class='jd-stat'><span class='jd-stat-label'>Link(s):</span>"
        f"<span class='jd-stat-val'>{lg_links}</span></span>"
        f"<span class='jd-stat'><span class='jd-stat-label'>Online:</span>"
        f"<span class='jd-stat-val' style='color:var(--green)'>{lg_pkgs - lg_errors}</span></span>"
        f"<span class='jd-stat'><span class='jd-stat-label'>Offline:</span>"
        f"<span class='jd-stat-val' style='color:#e06c75'>{lg_errors}</span></span>"
        f"</div>"
    )
    dl_statusbar = (
        f"<div class='jd-sb-row'>"
        f"<span class='jd-stat'><span class='jd-stat-label'>Package(s):</span>"
        f"<span class='jd-stat-val'>{dl_pkgs}</span></span>"
        f"<span class='jd-stat'><span class='jd-stat-label'>Running:</span>"
        f"<span class='jd-stat-val' style='color:var(--green)'>{dl_running}</span></span>"
        f"<span class='jd-stat'><span class='jd-stat-label'>Errors:</span>"
        f"<span class='jd-stat-val' style='color:#e06c75'>{dl_errors}</span></span>"
        f"</div>"
    )

    return (
        "<div id='pipeline' class='jd-wrap'>"
        # Toolbar
        "<div class='jd-toolbar'>"
        "<button class='jd-tb-btn' title='Resume all paused/error jobs' onclick='jdBulkAction(\"resume_all\")'>&#9654; Start All</button>"
        "<button class='jd-tb-btn' title='Pause all running jobs' onclick='jdBulkAction(\"pause_all\")'>&#9646;&#9646; Pause All</button>"
        "<div class='jd-tb-sep'></div>"
        "<button class='jd-tb-btn' title='Remove completed jobs' onclick='jdBulkAction(\"clear_done\")'>&#10005; Clear Done</button>"
        "<div class='jd-tb-sep'></div>"
        "<button class='jd-tb-btn' title='Refresh now' onclick='refresh()' style='margin-left:auto'>&#8635; Refresh</button>"
        "</div>"
        # Tabs
        "<div class='jd-tabbar'>"
        f"<div class='jd-tab' data-tab='linkgrabber' onclick='jdSwitchTab(\"linkgrabber\")'>"
        f"&#128279; LinkGrabber <span class='jd-badge'>{lg_pkgs}</span></div>"
        f"<div class='jd-tab active' data-tab='downloads' onclick='jdSwitchTab(\"downloads\")'>"
        f"&#11015; Downloads <span class='jd-badge'>{dl_pkgs}</span></div>"
        "</div>"
        # Panes
        f"<div id='jd-linkgrabber' class='jd-pane' style='display:none'>{lg_html}</div>"
        f"<div id='jd-downloads' class='jd-pane'>{dl_html}</div>"
        # Status bars
        f"<div id='jd-sb-linkgrabber' class='jd-statusbar' style='display:none'>{lg_statusbar}</div>"
        f"<div id='jd-sb-downloads' class='jd-statusbar'>{dl_statusbar}</div>"
        "</div>"
    )


def _grab_btns(token_esc: str) -> str:
    """Three tiny inline forms: STRM / MKV / MP4."""
    def btn(mode: str, container: str, label: str) -> str:
        cont_field = f"<input type='hidden' name='container' value='{container}'>" if mode == "download" else ""
        return (
            f"<form method='post' action='/api/manual-grab' class='task-actions' style='display:inline;margin:0'>"
            f"<input type='hidden' name='token' value='{token_esc}'>"
            f"<input type='hidden' name='output_mode' value='{mode}'>"
            f"{cont_field}"
            f"<button type='submit' class='jd-tb-btn' style='height:20px;font-size:10px'>{label}</button>"
            f"</form>"
        )
    return btn("strm", "", "STRM") + btn("download", "mkv", "MKV") + btn("download", "mp4", "MP4")


def _indexer_card(settings: Settings) -> tuple[str, int, int, int]:
    """LinkGrabber tab content.  Returns (html, pkg_count, link_count, error_count)."""
    from vn_source_gateway.infrastructure.activity import ActivityLog
    import time as _time

    now = int(_time.time())
    events = ActivityLog.get().recent(100)
    searches = [e for e in events if e.kind == "search"][:20]

    if not searches:
        return "<div class='jd-empty'>No indexer queries yet.</div>", 0, 0, 0

    # Deduplicate by title (keep most-recent)
    seen: dict[str, object] = {}
    for ev in searches:
        if ev.title not in seen:
            seen[ev.title] = ev
    deduped = list(seen.values())

    total_links = sum(
        len(getattr(ev, "grabs", []) or []) or (
            int(ev.detail.split(" result")[0].split()[-1])
            if " result" in ev.detail else 0
        )
        for ev in deduped
    )
    error_count = sum(1 for ev in deduped if ev.status != "ok")

    rows = []
    for ev in deduped:
        age = _time_ago(max(0, now - ev.ts))
        if ": " in ev.title:
            kind_prefix, show_title = ev.title.split(": ", 1)
        else:
            kind_prefix, show_title = "", ev.title
        dot_cls = "ok" if ev.status == "ok" else "err"
        results_part = ev.detail.split(" — ")[0] if " — " in ev.detail else ev.detail
        ev_grabs = getattr(ev, "grabs", []) or []
        ev_url = getattr(ev, "url", "") or ""
        link_btn = (
            f" <a href='{html.escape(ev_url)}' target='_blank' "
            f"style='font-size:10px;color:var(--accent)' title='Open XML'>↗</a>"
        ) if ev_url else ""

        if ev_grabs:
            shown = ev_grabs[:40]
            overflow = len(ev_grabs) - len(shown)
            grab_rows = ""
            for g in shown:
                tok = html.escape(g.get("token", ""), quote=True)
                t = g.get("title", "")
                for suf in (" [STRM]", " [HLS-DL]"):
                    if t.endswith(suf):
                        t = t[:-len(suf)]; break
                grab_rows += (
                    f"<div style='display:flex;align-items:center;gap:4px;padding:2px 0;"
                    f"border-bottom:1px solid var(--border)'>"
                    f"<span style='flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;"
                    f"white-space:nowrap;font-size:11px;color:var(--text)'>{html.escape(t)}</span>"
                    f"<span style='display:flex;gap:2px;flex-shrink:0'>{_grab_btns(tok)}</span>"
                    f"</div>"
                )
            if overflow > 0:
                grab_rows += f"<div style='font-size:11px;color:var(--muted);padding:2px 0'>…and {overflow} more</div>"
            xml_link = (
                f"<div style='margin-top:4px'>"
                f"<a href='{html.escape(ev_url)}' target='_blank' style='font-size:10px;color:var(--accent)'>↗ open XML</a>"
                f"</div>"
            ) if ev_url else ""
            results_cell = (
                f"<details class='pipe-detail'><summary>{html.escape(results_part)}</summary>"
                f"<div style='margin-top:4px;padding:6px 10px;background:rgba(0,0,0,0.25);"
                f"border-radius:5px;border:1px solid var(--border)'>"
                f"{grab_rows}{xml_link}</div></details>"
            )
        else:
            results_cell = (
                f"<span style='color:var(--muted);font-size:11px'>{html.escape(results_part)}</span>"
                f"{link_btn}"
            )

        rows.append(
            f"<tr>"
            f"<td style='white-space:nowrap;font-size:11px;color:var(--muted)'>{html.escape(show_title)}</td>"
            f"<td style='white-space:nowrap;font-size:11px;color:var(--muted)'>{html.escape(kind_prefix)}</td>"
            f"<td>{results_cell}</td>"
            f"<td style='white-space:nowrap;font-size:11px;color:var(--muted)'>{html.escape(age)}</td>"
            f"<td style='text-align:center'><span class='sdot {dot_cls}'></span></td>"
            f"</tr>"
        )

    body = (
        "<table class='jd-table'><thead><tr>"
        "<th>Name</th><th>Type</th><th>Results</th><th>When</th><th></th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )
    return body, len(deduped), total_links, error_count


def _download_card(settings: Settings) -> tuple[str, int, int, int]:
    """Downloads tab content.  Returns (html, pkg_count, running_count, error_count)."""
    from vn_source_gateway.infrastructure.activity import ActivityLog
    import time as _time

    now = int(_time.time())

    try:
        jobs = sorted(
            qbittorrent.torrents_info(settings),
            key=lambda x: x.get("added_on", 0), reverse=True,
        )[:25]
    except Exception:
        jobs = []

    events = ActivityLog.get().recent(100)
    events_by_ref: dict[str, list] = {}
    for ev in events:
        if ev.ref:
            events_by_ref.setdefault(ev.ref, []).append(ev)

    running_count = 0
    error_count = 0
    rows = []

    for job in jobs:
        state = str(job.get("state", ""))
        progress = float(job.get("progress", 0))
        task_hash = _attr(job.get("hash", ""))
        job_id = str(job.get("hash", ""))
        is_error = "error" in state.lower()
        error_msg = str(job.get("error", "") or "")
        save_path = str(job.get("save_path", "") or "")
        path_display = save_path.split("/")[-1] if save_path else "—"
        added_on = int(job.get("added_on", 0))
        age = _time_ago(max(0, now - added_on)) if added_on else ""

        if is_error:
            error_count += 1
            stage = "error"
        elif state in {"uploading", "pausedUP"}:
            stage = "done"
        elif state in {"downloading", "queuedDL"}:
            running_count += 1
            stage = "saving" if progress >= 0.35 else "matching"
        elif state == "pausedDL":
            stage = "paused"
        else:
            stage = "matching"

        if stage == "done":
            pct, bar_cls = 100, "done"
            status_txt = "Done"
            status_color = "var(--accent)"
        elif is_error:
            pct, bar_cls = max(5, int(progress * 100)), "fail"
            status_txt = f"Error — {error_msg[:50]}" if error_msg else "Error"
            status_color = "#e06c75"
        elif stage == "paused":
            pct, bar_cls = max(5, int(progress * 100)), "pulse"
            status_txt = f"Paused {int(progress * 100)}%"
            status_color = "var(--muted)"
        elif stage == "saving":
            pct, bar_cls = max(35, int(progress * 100)), "pulse"
            status_txt = f"Saving {int(progress * 100)}%…"
            status_color = "var(--green)"
        elif stage == "matching":
            pct, bar_cls = 15, "pulse"
            status_txt = "Resolving…"
            status_color = "var(--muted)"
        else:
            pct, bar_cls = 5, "pulse"
            status_txt = "Queued"
            status_color = "var(--muted)"

        progress_cell = (
            f"<div style='display:flex;flex-direction:column;gap:3px'>"
            f"<div class='pbar' style='width:140px'>"
            f"<div class='pbar-fill {bar_cls}' style='width:{pct}%'></div>"
            f"<div class='pbar-txt'>{pct}%</div>"
            f"</div></div>"
        )

        # Detail panel
        job_events = events_by_ref.get(job_id, [])
        grab_ev = next((e for e in job_events if e.kind == "grab"), None)
        resolved_ev = next((e for e in job_events if e.kind == "job" and "Resolved" in e.detail), None)
        done_ev = next((e for e in job_events if e.kind == "job" and "Done" in e.detail), None)

        match_msg = (resolved_ev.detail if resolved_ev
                     else (grab_ev.detail if grab_ev
                           else ("resolving…" if stage == "matching" else "—")))
        save_msg = (error_msg if is_error
                    else (f"writing… {int(progress * 100)}%" if stage == "saving"
                          else (done_ev.detail.replace("Done — ", "") if done_ev
                                else (save_path if save_path else "—"))))
        detail_html = _detail_panel([
            ("🔍", "Search",   "grabbed from Radarr/Sonarr", "ok"),
            ("⚙",  "Matching", match_msg, "ok" if (resolved_ev or grab_ev) else ""),
            ("💾", "Saving",   save_msg,  "error" if is_error else ("ok" if done_ev or stage == "done" else "")),
            ("✓",  "Done",     "completed" if stage == "done" else "", "ok" if stage == "done" else ""),
        ], open_by_default=(is_error or stage not in {"done"}))

        source = (grab_ev.detail if grab_ev
                  else str(job.get("tags", "") or job.get("category", "") or "—"))

        # Action buttons
        btns = ""
        if is_error:
            btns += "<button type='submit' name='action' value='resume' class='jd-tb-btn'>Retry</button>"
        elif state in {"downloading", "queuedDL"}:
            btns += "<button type='submit' name='action' value='pause' class='jd-tb-btn'>Pause</button>"
        elif state == "pausedDL":
            btns += "<button type='submit' name='action' value='resume' class='jd-tb-btn'>Resume</button>"
        btns += "<button type='submit' name='action' value='delete' class='jd-tb-btn' style='color:#e06c75;border-color:rgba(224,108,117,0.4)'>Delete</button>"

        name_cell = (
            f"<div style='font-weight:500;font-size:12px'>{html.escape(str(job.get('name', '')))}</div>"
            + (f"<div style='font-size:10px;color:var(--muted);margin-top:1px'>{html.escape(age)}</div>" if age else "")
            + detail_html
        )

        rows.append(
            f"<tr>"
            f"<td>{name_cell}</td>"
            f"<td style='white-space:nowrap'>{progress_cell}</td>"
            f"<td style='font-size:11px;color:{status_color};white-space:nowrap'>{html.escape(status_txt)}</td>"
            f"<td style='font-size:11px;color:var(--muted)'>{html.escape(source)}</td>"
            f"<td style='font-size:11px;color:var(--muted)' title='{_attr(save_path)}'>{html.escape(path_display)}</td>"
            f"<td style='white-space:nowrap'>"
            f"<form method='post' action='/tasks/action' class='task-actions' style='display:flex;gap:4px'>"
            f"<input type='hidden' name='hashes' value='{task_hash}'>"
            f"{btns}</form></td>"
            f"</tr>"
        )

    if not rows:
        body = "<div class='jd-empty'>No download tasks yet.</div>"
    else:
        body = (
            "<table class='jd-table'><thead><tr>"
            "<th>Name</th><th>Progress</th><th>Status</th>"
            "<th>Source</th><th>Save to</th><th>Actions</th>"
            "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
        )

    return body, len(jobs), running_count, error_count


def _pipeline_steps(stage: str, is_error: bool, progress: float) -> str:
    # stages in order
    STAGES = [
        ("search",   "Search"),
        ("matching", "Matching"),
        ("saving",   "Saving"),
        ("done",     "Done"),
    ]
    ORDER = [s for s, _ in STAGES]

    if is_error:
        # find last completed stage before error
        cur_idx = ORDER.index("matching") if stage == "error" else 0
    else:
        cur_idx = ORDER.index(stage) if stage in ORDER else 0

    parts = []
    for i, (key, label) in enumerate(STAGES):
        if is_error and i == cur_idx:
            cls = "ps-error"
        elif i < cur_idx or (not is_error and stage == "done"):
            cls = "ps-done"
        elif i == cur_idx:
            cls = "ps-active"
        else:
            cls = "ps-pending"

        # progress % inside active saving step
        extra = ""
        if key == "saving" and stage == "saving" and not is_error:
            pct = int(progress * 100)
            extra = f" {pct}%"

        parts.append(f"<span class='ps {cls}'>{label}{extra}</span>")
        if i < len(STAGES) - 1:
            parts.append("<span class='ps-sep'>›</span>")

    return "<span class='pipeline'>" + "".join(parts) + "</span>"
