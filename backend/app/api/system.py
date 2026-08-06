import os
import signal
from collections.abc import Callable

from fastapi import APIRouter, BackgroundTasks, Depends

router = APIRouter(prefix="/system", tags=["system"])


def _terminate_process() -> None:
    os.kill(os.getpid(), signal.SIGTERM)


def get_shutdown_handler() -> Callable[[], None]:
    return _terminate_process


@router.post("/shutdown", status_code=202)
def shutdown(
    background_tasks: BackgroundTasks,
    handler: Callable[[], None] = Depends(get_shutdown_handler),
) -> dict[str, str]:
    background_tasks.add_task(handler)
    return {"status": "shutting_down"}
