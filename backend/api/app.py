from __future__ import annotations

import pathlib

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .routers import actions, grab, manual_grab, pipeline, qbittorrent, source_test, torznab
from .routers import auth_router

_DIST = pathlib.Path(__file__).parent.parent.parent / "dist"

# Paths that bypass session auth entirely:
#  • /api/auth/*   — login / setup / logout / status
#  • /api/v2/*     — qBittorrent-compat API called by Radarr/Sonarr (uses QB credentials)
#  • everything else not starting with /api/ (torznab, grab, static SPA)
_AUTH_SKIP_PREFIXES = ("/api/auth/", "/api/v2/")


class _AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
        path = request.url.path

        # Non-API routes and explicitly skipped prefixes pass through
        if not path.startswith("/api/") or any(path.startswith(p) for p in _AUTH_SKIP_PREFIXES):
            return await call_next(request)  # type: ignore[operator]

        # Lazy import to avoid circular deps at module load time
        from backend.infrastructure.config import Settings
        from backend.infrastructure.auth import verify_session, COOKIE_NAME

        settings = Settings.load()
        # Auth not configured yet → allow everything (setup flow)
        if not settings.auth_username or not settings.auth_password_hash:
            return await call_next(request)  # type: ignore[operator]

        token = request.cookies.get(COOKIE_NAME)
        if token and verify_session(token):
            return await call_next(request)  # type: ignore[operator]

        return JSONResponse({"error": "Unauthorized"}, status_code=401)


def create_app() -> FastAPI:
    app = FastAPI(title="Deceptarr", docs_url=None, redoc_url=None)

    app.add_middleware(_AuthMiddleware)

    # Auth routes (no session required)
    app.include_router(auth_router.router)

    # API routers — always active
    app.include_router(torznab.router)
    app.include_router(grab.router)
    app.include_router(qbittorrent.router)
    app.include_router(actions.router)
    app.include_router(source_test.router)
    app.include_router(manual_grab.router)
    app.include_router(pipeline.router)

    if _DIST.is_dir():
        # Serve hashed JS/CSS assets from /assets/* with correct caching headers
        _assets_dir = _DIST / "assets"
        if _assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")

        # SPA catch-all: serve index.html for every non-API route so that
        # Vue Router's createWebHistory() works on direct URL navigation.
        # This must be the LAST route registered.
        _index_html = _DIST / "index.html"

        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str) -> Response:
            from fastapi.responses import FileResponse
            return FileResponse(str(_index_html), media_type="text/html")
    else:
        @app.get("/{full_path:path}")
        def frontend_missing(full_path: str) -> JSONResponse:
            return JSONResponse(
                {
                    "service": "deceptarr",
                    "status": "ok",
                    "frontend": "missing dist build",
                    "hint": "Run npm run build in frontend/ or use the Vite dev server.",
                }
            )

    return app
