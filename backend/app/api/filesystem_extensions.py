from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_claude_home_path, get_global_settings_path
from app.checkpoint_reader import CHECKPOINT_COVERAGE_CAVEAT, extract_checkpoints
from app.library_registry import scan_library
from app.memory_reader import read_project_memory
from app.rules_inspector import scan_rules
from app.sandbox_config import read_sandbox_config
from app.telemetry_reader.project_paths import encode_project_path

router = APIRouter(tags=["filesystem-extensions"])


@router.get("/memory")
def get_memory(
    project_path: str = Query(...),
    claude_home: Path = Depends(get_claude_home_path),
) -> dict:
    memory = read_project_memory(claude_home / "projects", project_path)
    if memory is None:
        raise HTTPException(status_code=404, detail="No auto memory found for this project")
    return {
        "index_content": memory.index_content,
        "topics": [
            {
                "filename": t.filename,
                "name": t.name,
                "description": t.description,
                "metadata": t.metadata,
                "content": t.content,
                "modified": t.modified,
            }
            for t in memory.topics
        ],
    }


@router.get("/rules")
def get_rules(
    project_path: str | None = Query(default=None),
    claude_home: Path = Depends(get_claude_home_path),
) -> list[dict]:
    project_dir = Path(project_path) if project_path else None
    rules = scan_rules(claude_home, project_dir)
    return [
        {
            "name": r.name,
            "scope": r.scope,
            "relative_folder": r.relative_folder,
            "paths": r.paths,
            "file_path": r.file_path,
        }
        for r in rules
    ]


@router.get("/checkpoints/{session_id}")
def get_checkpoints(
    session_id: str,
    cwd: str = Query(...),
    claude_home: Path = Depends(get_claude_home_path),
) -> dict:
    transcript_path = claude_home / "projects" / encode_project_path(cwd) / f"{session_id}.jsonl"
    checkpoints = extract_checkpoints(transcript_path)
    return {
        "checkpoints": [
            {
                "message_id": c.message_id,
                "timestamp": c.timestamp,
                "changed_files": c.changed_files,
            }
            for c in checkpoints
        ],
        "coverage_caveat": CHECKPOINT_COVERAGE_CAVEAT,
    }


@router.get("/sandbox/config")
def get_sandbox_config(
    settings_path: Path = Depends(get_global_settings_path),
) -> dict:
    config = read_sandbox_config(settings_path)
    return {
        "enabled": config.enabled,
        "raw_config": config.raw_config,
        "auto_allow_bash_if_sandboxed": config.auto_allow_bash_if_sandboxed,
    }


@router.get("/output-styles")
def get_output_styles(
    project_path: str | None = Query(default=None),
    claude_home: Path = Depends(get_claude_home_path),
) -> list[dict]:
    project_dir = Path(project_path) if project_path else None
    items = scan_library(claude_home, project_dir)
    return [
        {
            "id": item.id,
            "scope": item.scope,
            "name": item.name,
            "description": item.description,
            "path": item.path,
        }
        for item in items
        if item.resource_type == "output_style"
    ]
