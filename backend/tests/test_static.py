from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.static import mount_frontend


def test_mount_frontend_serves_index_when_dist_exists(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html><body>control plane</body></html>")

    app = FastAPI()
    mounted = mount_frontend(app, tmp_path)
    client = TestClient(app)

    response = client.get("/")

    assert mounted is True
    assert response.status_code == 200
    assert "control plane" in response.text


def test_mount_frontend_is_a_noop_when_dist_is_missing(tmp_path: Path) -> None:
    missing_dist = tmp_path / "does-not-exist"

    app = FastAPI()
    mounted = mount_frontend(app, missing_dist)
    client = TestClient(app)

    response = client.get("/")

    assert mounted is False
    assert response.status_code == 404
