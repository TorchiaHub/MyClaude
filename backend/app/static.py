from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def mount_frontend(app: FastAPI, dist_path: Path) -> bool:
    if not dist_path.is_dir():
        return False
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
    return True
