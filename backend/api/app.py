from __future__ import annotations

import pathlib

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routers import actions, grab, manual_grab, qbittorrent, source_test, torznab

_DIST = pathlib.Path(__file__).parent.parent.parent / "dist"


def create_app() -> FastAPI:
    app = FastAPI(title="Deceptarr", docs_url=None, redoc_url=None)

    # API routers — always active
    app.include_router(torznab.router)
    app.include_router(grab.router)
    app.include_router(qbittorrent.router)
    app.include_router(actions.router)
    app.include_router(source_test.router)
    app.include_router(manual_grab.router)

    if _DIST.is_dir():
        # Phase 2: compiled Vue SPA in dist/ — serve as static files
        app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="spa")
    else:
        # Phase 1: fall back to Python-rendered HTML while Vue is not built
        from .routers import ui_routes
        app.include_router(ui_routes.router)

    return app
