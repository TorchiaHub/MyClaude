from pathlib import Path

from fastapi import FastAPI

from app.api import (
    activity,
    claude_home,
    config,
    filesystem_extensions,
    health,
    hooks,
    library,
    mcp,
    packages,
    projects,
    system,
    telemetry,
)
from app.origin_guard import OriginGuardMiddleware
from app.static import mount_frontend

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    app = FastAPI(title="Claude Code Control Plane")
    app.add_middleware(OriginGuardMiddleware)
    app.include_router(health.router)
    app.include_router(system.router)
    app.include_router(config.router)
    app.include_router(mcp.router)
    app.include_router(library.router)
    app.include_router(projects.router)
    app.include_router(telemetry.router)
    app.include_router(packages.router)
    app.include_router(activity.router)
    app.include_router(hooks.router)
    app.include_router(filesystem_extensions.router)
    app.include_router(claude_home.router)
    mount_frontend(app, FRONTEND_DIST)
    return app


app = create_app()
