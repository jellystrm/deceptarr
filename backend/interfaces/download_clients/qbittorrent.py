from __future__ import annotations

import os
import threading
import time
from typing import Any

from backend.application.grab_service import process_job
from backend.domain.models import GatewayJob
from backend.infrastructure.config import Settings
from backend.infrastructure.jobs import JobStore


def torrents_info(
    settings: Settings,
    category: str | None = None,
    hashes: str | None = None,
) -> list[dict[str, Any]]:
    jobs = JobStore(settings.state_path).list_jobs()
    if category in {"all", ""}:
        category = None
    wanted_hashes = {part.strip() for part in hashes.split("|") if part.strip()} if hashes else None
    result: list[dict[str, Any]] = []
    for job in jobs:
        if job.status == "deleted":
            continue
        if wanted_hashes is not None and job.job_id not in wanted_hashes:
            continue
        qbit_job = _job_to_qbit(job)
        if category and qbit_job["category"] != category:
            continue
        result.append(qbit_job)
    return result


def pause(settings: Settings, hashes: str, paused: bool) -> None:
    store = JobStore(settings.state_path)
    for job_id in _hashes(settings, hashes):
        job = store.get(job_id)
        if not job:
            continue
        if paused:
            store.update(job_id, paused=True)
            continue
        # Resume == retry: re-queue and re-run unless the job is already done.
        # Covers queued, error, and zombie "running" jobs (thread died on restart).
        if job.status in {"queued", "error", "running"}:
            store.update(job_id, paused=False, status="queued", progress=0.0, error=None)
            threading.Thread(
                target=process_job, args=(settings, job_id),
                name=f"deceptarr-job-{job_id[:8]}", daemon=True,
            ).start()
        else:
            store.update(job_id, paused=False)


def delete(settings: Settings, hashes: str, delete_files: bool = False) -> None:
    store = JobStore(settings.state_path)
    for job_id in _hashes(settings, hashes):
        job = store.get(job_id)
        if job:
            if delete_files and job.save_path and os.path.exists(job.save_path):
                try:
                    os.remove(job.save_path)
                except IsADirectoryError:
                    pass
            store.update(job_id, status="deleted", progress=0.0)


def preferences(settings: Settings) -> dict[str, Any]:
    return {
        "save_path": settings.download_root,
        "temp_path": settings.download_root,
        "temp_path_enabled": False,
        "scan_dirs": {},
        "export_dir": "",
        "mail_notification_enabled": False,
        "web_ui_domain_list": "*",
        "web_ui_address": settings.ui_host,
        "web_ui_port": settings.ui_port,
        "bypass_local_auth": True,
        "use_https": False,
        "max_connec": -1,
        "max_connec_per_torrent": -1,
        "max_uploads": -1,
        "max_uploads_per_torrent": -1,
        "dl_limit": 0,
        "up_limit": 0,
    }


def build_info() -> dict[str, Any]:
    return {"qt": "6.6.0", "libtorrent": "2.0.9", "boost": "1.83.0", "openssl": "3.0.0", "bitness": 64}


def categories(settings: Settings) -> dict[str, Any]:
    return {
        "radarr": {"name": "radarr", "savePath": settings.download_root},
        "sonarr": {"name": "sonarr", "savePath": settings.download_root},
        "deceptarr": {"name": "deceptarr", "savePath": settings.download_root},
    }


def transfer_info() -> dict[str, int]:
    return {"dl_info_speed": 0, "up_info_speed": 0, "dl_info_data": 0, "up_info_data": 0}


def sync_maindata(settings: Settings, category: str | None = None) -> dict[str, Any]:
    return {"torrents": {job["hash"]: job for job in torrents_info(settings, category=category)}}


def _job_to_qbit(job: GatewayJob) -> dict[str, Any]:
    if job.paused and job.status in {"queued", "running"}:
        state = "pausedDL"
        progress = job.progress
    elif job.status == "completed":
        state = "uploading"
        progress = 1.0
    elif job.status == "error":
        state = "error"
        progress = 0.0
    elif job.status == "running":
        state = "downloading"
        progress = max(0.01, job.progress)
    else:
        state = "queuedDL"
        progress = 0.0
    now = int(time.time())
    return {
        "hash": job.job_id,
        "name": _job_name(job),
        "category": _job_category(job),
        "state": state,
        "progress": progress,
        "size": 1024 * 1024 * 1024,
        "completed": int(progress * 1024 * 1024 * 1024),
        "amount_left": 0 if progress >= 1 else int((1 - progress) * 1024 * 1024 * 1024),
        "save_path": job.save_path or "",
        "content_path": job.save_path or "",
        "completion_path": job.save_path or "",
        "ratio": 1,
        "dlspeed": 0,
        "upspeed": 0,
        "eta": 0,
        "priority": 0,
        "added_on": job.created_at,
        "completion_on": job.updated_at if job.status == "completed" else 0,
        "last_activity": job.updated_at,
        "tracker": "deceptarr",
        "tags": "strm" if job.release.output_mode == "strm" else "hls-dl",
        "seq_dl": False,
        "f_l_piece_prio": False,
        "seen_complete": job.updated_at if job.status == "completed" else now,
    }


def _job_name(job: GatewayJob) -> str:
    suffix = "STRM" if job.release.output_mode == "strm" else "HLS-DL"
    return f"{job.release.title} [{suffix}]"


def _job_category(job: GatewayJob) -> str:
    category = (job.category or "").strip()
    if category and category != "deceptarr":
        return category
    return "radarr" if job.release.kind == "movie" else "sonarr"


def _hashes(settings: Settings, hashes: str) -> list[str]:
    if hashes == "all":
        return [job.job_id for job in JobStore(settings.state_path).list_jobs()]
    normalized = hashes.replace(",", "|")
    return [part.strip() for part in normalized.split("|") if part.strip()]
