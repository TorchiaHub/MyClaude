from pathlib import Path

from fastapi import FastAPI

from app.api import config, health, library, mcp, projects, system
from app.static import mount_frontend

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    app = FastAPI(title="Claude Code Control Plane")
    app.include_router(health.router)
    app.include_router(system.router)
    app.include_router(config.router)
    app.include_router(mcp.router)
    app.include_router(library.router)
    app.include_router(projects.router)
    mount_frontend(app, FRONTEND_DIST)
    return app


app = create_app()
