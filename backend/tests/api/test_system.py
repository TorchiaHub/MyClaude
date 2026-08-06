from fastapi.testclient import TestClient

from app.api.system import get_shutdown_handler
from app.main import app


def test_shutdown_returns_202_and_shutting_down_status():
    app.dependency_overrides[get_shutdown_handler] = lambda: (lambda: None)

    client = TestClient(app)
    response = client.post("/system/shutdown")

    app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json() == {"status": "shutting_down"}


def test_shutdown_invokes_the_injected_handler():
    handler_calls = []

    def fake_handler():
        handler_calls.append(True)

    app.dependency_overrides[get_shutdown_handler] = lambda: fake_handler

    client = TestClient(app)
    client.post("/system/shutdown")

    app.dependency_overrides.clear()

    assert handler_calls == [True]
