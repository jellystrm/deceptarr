"""LinkGrabber pane — tree view of recent Torznab search results."""
from __future__ import annotations

import html
import json
import time

from backend.infrastructure.config import Settings


def _time_ago(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def _grab_btns(token_esc: str) -> str:
    def btn(mode: str, container: str, label: str) -> str:
        cont = f"<input type='hidden' name='container' value='{container}'>" if mode == "download" else ""
        return (
            f"<form method='post' action='/api/manual-grab' class='task-actions' style='display:inline;margin:0'>"
            f"<input type='hidden' name='token' value='{token_esc}'>"
            f"<input type='hidden' name='output_mode' value='{mode}'>"
            f"{cont}"
            f"<button type='submit' class='jd-tb-btn' style='height:20px;font-size:10px'>{label}</button>"
            f"</form>"
        )
    return btn("strm", "", "STRM") + btn("download", "mkv", "MKV") + btn("download", "mp4", "MP4")


def _bulk_grab_btns(tokens: list[str]) -> str:
    toks_esc = html.escape(json.dumps(tokens), quote=True)

    def btn(mode: str, container: str, label: str) -> str:
        cont = f"<input type='hidden' name='container' value='{container}'>" if mode == "download" else ""
        return (
            f"<form method='post' action='/api/manual-grab-bulk' class='task-actions' style='display:inline;margin:0'>"
            f"<input type='hidden' name='tokens' value='{toks_esc}'>"
            f"<input type='hidden' name='output_mode' value='{mode}'>"
            f"{cont}"
            f"<button type='submit' class='jd-tb-btn' style='height:20px;font-size:10px'>{label}</button>"
            f"</form>"
        )
    return btn("strm", "", "STRM") + btn("download", "mkv", "MKV") + btn("download", "mp4", "MP4")


def _build_grab_tree(grabs: list[dict]) -> list[dict]:
    from backend.application.grab_service import decode_release

    seen: dict[tuple, dict] = {}
    for g in grabs:
        tok = g.get("token", "")
        title = g.get("title", "")
        for suf in (" [STRM]", " [HLS-DL]"):
            if title.endswith(suf):
                title = title[: -len(suf)]
                break
        try:
            r = decode_release(tok)
        except Exception:
            continue
        key = (r.source_name, r.kind, r.season_number, r.episode_number)
        existing = seen.get(key)
        if not existing or r.output_mode == "strm":
            seen[key] = {"title": title, "token": tok, "r": r}

    decoded = list(seen.values())
    pkg_map: dict[tuple, dict] = {}

    for item in decoded:
        r = item["r"]
        if r.kind == "movie":
            key = ("mv", r.source_name, r.title)
            if key not in pkg_map:
                pkg_map[key] = {"title": item["title"], "pkg_token": item["token"],
                                "ep_tokens": [item["token"]], "children": [], "kind": "movie"}
        elif r.kind == "episode" and r.episode_number is None:
            key = ("tv", r.source_name, r.season_number)
            if key not in pkg_map:
                pkg_map[key] = {"title": item["title"], "pkg_token": item["token"],
                                "ep_tokens": [], "children": [], "kind": "episode"}
            else:
                pkg_map[key]["title"] = item["title"]
                pkg_map[key]["pkg_token"] = item["token"]

    for item in decoded:
        r = item["r"]
        if r.kind != "episode" or r.episode_number is None:
            continue
        key = ("tv", r.source_name, r.season_number)
        if key not in pkg_map:
            s = r.season_number
            auto = f"{r.source_name or ''} S{s:02d}" if s is not None else f"{r.source_name or ''} S??"
            pkg_map[key] = {"title": auto, "pkg_token": item["token"],
                            "ep_tokens": [], "children": [], "kind": "episode"}
        pkg_map[key]["ep_tokens"].append(item["token"])
        pkg_map[key]["children"].append(item)

    for pkg in pkg_map.values():
        pkg["children"].sort(key=lambda x: (x["r"].episode_number or 0))
    return list(pkg_map.values())


def indexer_pane(settings: Settings) -> tuple[str, int, int, int]:
    """Returns (html, pkg_count, link_count, error_count)."""
    from backend.infrastructure.activity import ActivityLog

    now = int(time.time())
    events = ActivityLog.get().recent(100)
    searches = [e for e in events if e.kind == "search"][:20]
    if not searches:
        return "<div class='jd-empty'>No indexer queries yet.</div>", 0, 0, 0

    seen_ev: dict[str, object] = {}
    for ev in searches:
        if ev.title not in seen_ev:
            seen_ev[ev.title] = ev
    deduped = list(seen_ev.values())

    error_count = sum(1 for ev in deduped if ev.status != "ok")
    total_pkgs, total_links, pkg_counter = 0, 0, 0
    rows: list[str] = []

    for ev in deduped:
        age = _time_ago(max(0, now - ev.ts))
        ev_grabs = getattr(ev, "grabs", []) or []
        ev_url = getattr(ev, "url", "") or ""
        dot_cls = "ok" if ev.status == "ok" else "err"
        kind_prefix, show_title = ev.title.split(": ", 1) if ": " in ev.title else ("", ev.title)

        if not ev_grabs:
            detail = ev.detail.split(" — ")[0] if " — " in ev.detail else ev.detail
            rows.append(
                f"<tr style='background:rgba(0,0,0,0.06)'>"
                f"<td style='font-size:11px;color:var(--text);padding:5px 8px' colspan='2'>"
                f"{html.escape(show_title)} <span style='color:var(--muted)'>— {html.escape(detail)}</span></td>"
                f"<td></td><td style='font-size:11px;color:var(--muted);white-space:nowrap'>{html.escape(age)}</td>"
                f"<td style='text-align:center'><span class='sdot {dot_cls}'></span></td></tr>"
            )
            continue

        packages = _build_grab_tree(ev_grabs)
        if not packages:
            continue

        n_pkgs, n_links = len(packages), sum(max(len(p["ep_tokens"]), 1) for p in packages)
        total_pkgs += n_pkgs
        total_links += n_links
        xml_a = (f" <a href='{html.escape(ev_url)}' target='_blank' "
                 f"style='font-size:10px;color:var(--accent)' title='Open XML'>↗</a>") if ev_url else ""

        rows.append(
            f"<tr style='background:rgba(0,0,0,0.14)'>"
            f"<td style='font-size:11px;font-weight:600;color:var(--text);padding:5px 10px'>"
            f"{html.escape(show_title)}{xml_a}</td>"
            f"<td style='font-size:10px;color:var(--muted);white-space:nowrap'>"
            f"{html.escape(kind_prefix)} &middot; {n_pkgs} pkg &middot; {n_links} links</td>"
            f"<td></td><td style='font-size:11px;color:var(--muted);white-space:nowrap'>{html.escape(age)}</td>"
            f"<td style='text-align:center'><span class='sdot {dot_cls}'></span></td></tr>"
        )

        for pkg in packages:
            pkg_id = f"lg{pkg_counter}"
            pkg_counter += 1
            children = pkg["children"]
            ep_tokens = pkg["ep_tokens"] or [pkg["pkg_token"]]
            has_ch = bool(children)
            count_txt = f"{len(children)} ep" if children else ""
            btns = _bulk_grab_btns(ep_tokens)
            if has_ch:
                arrow = f"<span class='jd-tree-arr' id='jd-arr-{pkg_id}' style='color:var(--muted)'>&#9658;</span>"
                toggle = f"onclick='jdTogglePkg(\"{pkg_id}\")'"
            else:
                arrow = "<span style='display:inline-block;width:12px'></span>"
                toggle = ""
            rows.append(
                f"<tr class='jd-pkg-row' {toggle}>"
                f"<td style='padding:4px 8px 4px 20px'><div style='display:flex;align-items:center;gap:6px'>"
                f"{arrow}<span style='font-size:12px;font-weight:500'>{html.escape(pkg['title'])}</span>"
                f"</div></td><td style='font-size:10px;color:var(--muted);white-space:nowrap'>{count_txt}</td>"
                f"<td style='white-space:nowrap'>{btns}</td><td></td><td></td></tr>"
            )
            for child in children:
                r = child["r"]
                ep_n = r.episode_number
                ep_label = f"E{ep_n:02d}" if ep_n is not None else child["title"]
                tok_esc = html.escape(child["token"], quote=True)
                rows.append(
                    f"<tr class='jd-child-r jd-c-{pkg_id}' style='display:none'>"
                    f"<td style='padding:3px 8px 3px 42px;font-size:11px;color:var(--muted)'>"
                    f"{html.escape(ep_label)}</td><td></td>"
                    f"<td style='white-space:nowrap'>{_grab_btns(tok_esc)}</td><td></td><td></td></tr>"
                )

    if not rows:
        return "<div class='jd-empty'>No indexer queries yet.</div>", 0, 0, 0

    body = (
        "<table class='jd-table'><thead><tr>"
        "<th style='padding-left:20px'>Name</th><th>Info</th><th>Actions</th><th>When</th><th></th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )
    return body, total_pkgs, total_links, error_count
