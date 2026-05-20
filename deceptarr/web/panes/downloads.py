"""Downloads pane — tree view of active/completed download jobs."""
from __future__ import annotations

import html

from deceptarr.infrastructure.config import Settings
from deceptarr.web.cards import _attr


def download_pane(settings: Settings) -> tuple[str, int, int, int]:
    """Returns (html, pkg_count, running_count, error_count)."""
    from deceptarr.infrastructure.jobs import JobStore

    store = JobStore(settings.state_path)
    all_jobs = sorted(store.list_jobs(), key=lambda j: j.created_at, reverse=True)[:200]
    if not all_jobs:
        return "<div class='jd-empty'>No download tasks yet.</div>", 0, 0, 0

    pkg_order: list[tuple] = []
    pkg_map: dict[tuple, dict] = {}
    for job in all_jobs:
        r = job.release
        if r.kind == "movie":
            year = f" ({r.year})" if r.year else ""
            key: tuple = ("mv", r.title)
            label = f"{r.title}{year}"
        else:
            s = r.season_number if r.season_number is not None else 0
            key = ("tv", r.title, s)
            label = f"{r.title} S{s:02d}"
        if key not in pkg_map:
            pkg_order.append(key)
            pkg_map[key] = {"label": label, "kind": r.kind, "jobs": []}
        pkg_map[key]["jobs"].append(job)

    running_count = error_count = 0
    rows: list[str] = []

    for pi, key in enumerate(pkg_order):
        pkg_id = f"dl{pi}"
        pkg = pkg_map[key]
        jobs = pkg["jobs"]
        n_total = len(jobs)
        n_done = sum(1 for j in jobs if j.status == "completed")
        n_running = sum(1 for j in jobs if j.status == "running")
        n_error = sum(1 for j in jobs if j.status == "error")
        n_queued = sum(1 for j in jobs if j.status == "queued")
        running_count += n_running
        if n_error > 0:
            error_count += 1

        if n_error > 0:
            pkg_status = f"<span style='color:#e06c75'>{n_error} error{'s' if n_error > 1 else ''}</span>"
        elif n_running > 0:
            pkg_status = (
                f"<span style='color:var(--green)'>{n_done}/{n_total}"
                f"<span style='color:var(--muted)'> &middot; {n_running} running</span></span>"
            )
        elif n_queued > 0:
            pkg_status = f"<span style='color:var(--muted)'>{n_done}/{n_total} &middot; {n_queued} queued</span>"
        elif n_done == n_total:
            pkg_status = f"<span style='color:var(--accent)'>&#10003; {n_done}/{n_total}</span>"
        else:
            pkg_status = f"<span style='color:var(--muted)'>{n_done}/{n_total}</span>"

        has_ch = n_total > 1
        toggle = f"onclick='jdTogglePkg(\"{pkg_id}\")'" if has_ch else ""
        arrow = (
            f"<span class='jd-tree-arr' id='jd-arr-{pkg_id}' style='color:var(--muted)'>&#9658;</span>"
            if has_ch else "<span style='display:inline-block;width:12px'></span>"
        )
        rows.append(
            f"<tr class='jd-pkg-row' {toggle}>"
            f"<td style='padding:5px 10px'><div style='display:flex;align-items:center;gap:6px'>"
            f"{arrow}<span style='font-size:12px;font-weight:500'>{html.escape(pkg['label'])}</span>"
            f"</div></td><td colspan='4' style='font-size:11px;padding:5px 10px'>{pkg_status}</td></tr>"
        )

        def _sort_key(j: object) -> tuple:
            rel = j.release  # type: ignore[attr-defined]
            return (
                rel.season_number if rel.season_number is not None else 0,
                rel.episode_number if rel.episode_number is not None else 0,
                rel.source_name or "",
            )

        for job in sorted(jobs, key=_sort_key):
            r = job.release
            if r.kind == "episode":
                ep_n = r.episode_number
                ep_label = (f"E{ep_n:02d}" if ep_n is not None else "Season Pack")
                if r.source_name:
                    ep_label += f"  ·  {r.source_name}"
            else:
                ep_label = r.title

            progress = job.progress or 0.0
            status = job.status
            is_err = status == "error"
            if is_err:
                pct = max(5, int(progress * 100))
                bar_cls, status_txt = "fail", (f"Error — {job.error[:40]}" if job.error else "Error")
                status_color = "#e06c75"
            elif status == "completed":
                pct, bar_cls, status_txt, status_color = 100, "done", "Done", "var(--accent)"
            elif status == "running":
                pct = max(5, int(progress * 100))
                bar_cls, status_txt, status_color = "pulse", f"{pct}%", "var(--green)"
            elif status == "paused":
                pct = max(5, int(progress * 100))
                bar_cls, status_txt, status_color = "pulse", "Paused", "var(--muted)"
            else:
                pct, bar_cls, status_txt, status_color = 5, "pulse", "Queued", "var(--muted)"

            pbar = (
                f"<div class='pbar' style='width:100px'>"
                f"<div class='pbar-fill {bar_cls}' style='width:{pct}%'></div>"
                f"<div class='pbar-txt'>{pct}%</div></div>"
            )
            task_hash = _attr(job.job_id)
            btns = ""
            if is_err:
                btns += "<button type='submit' name='action' value='resume' class='jd-tb-btn'>Retry</button>"
            elif status == "running":
                btns += "<button type='submit' name='action' value='pause' class='jd-tb-btn'>Pause</button>"
            elif status in {"paused", "queued"}:
                btns += "<button type='submit' name='action' value='resume' class='jd-tb-btn'>Resume</button>"
            btns += (
                "<button type='submit' name='action' value='delete' class='jd-tb-btn'"
                " style='color:#e06c75;border-color:rgba(224,108,117,0.4)'>&#10005;</button>"
            )
            save_path = job.save_path or ""
            path_display = save_path.split("/")[-1] if save_path else "—"
            rows.append(
                f"<tr class='jd-child-r jd-c-{pkg_id}' style='display:none'>"
                f"<td style='padding:3px 8px 3px 28px;font-size:11px;color:var(--muted)'>{html.escape(ep_label)}</td>"
                f"<td style='padding:3px 8px'>{pbar}</td>"
                f"<td style='font-size:11px;color:{status_color};white-space:nowrap'>{html.escape(status_txt)}</td>"
                f"<td style='font-size:10px;color:var(--muted);white-space:nowrap' title='{_attr(save_path)}'>"
                f"{html.escape(path_display)}</td>"
                f"<td style='white-space:nowrap'>"
                f"<form method='post' action='/tasks/action' class='task-actions' style='display:flex;gap:4px'>"
                f"<input type='hidden' name='hashes' value='{task_hash}'>{btns}</form></td></tr>"
            )

    body = (
        "<table class='jd-table'><thead><tr>"
        "<th style='padding-left:10px'>Package</th><th>Progress</th><th>Status</th><th>File</th><th>Actions</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )
    return body, len(pkg_order), running_count, error_count
