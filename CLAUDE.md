# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

Fase 0 (bootstrap), Fase 1 (core backend), Fase 2 (UI base + telemetry), Fase 3 (canvas, activation engine, live activity monitor), Fase 4 (workflow comparator), and Fase 5 (read-mostly filesystem-extension panels) of the implementation plan are done. `backend/` (FastAPI) exposes APIs backed by real Claude Code data — `config_reader`, `mcp_manager` (incl. add/remove/test-reachability), `library_registry`, `project_discovery`, `telemetry_reader` (transcript `.jsonl` parsing + cumulative usage from `~/.claude.json`), `package_registry` (CRUD for canvas-composed packages, content materialized on the real filesystem), `activation_engine` (merge/append into real Claude Code folders with a `written_files` sha256 manifest so manual user edits are never silently deleted, plus the single-active-global-package invariant), `activity_monitor` (session registry + tool_use drill-down, incl. `WS /activity/live`), `hooks_installer` (install/uninstall an additive `SessionStart` hook entry in `~/.claude/settings.json`, port-aware via `PORT` env var matching `start.sh`), `comparator` (static composition diff between two packages + two historical modes — "isolated" and "combination" — that reconstruct activation windows from `activation_log` and cross them with real transcript timestamps), `memory_reader` (per-project MEMORY.md index + topic-file frontmatter), `rules_inspector` (scans user- and project-level `.claude/rules/*.md`, incl. scoped `paths:` patterns), `checkpoint_reader` (reconstructs a checkpoint timeline from transcript `file-history-snapshot`/`file-history-delta` records, always surfacing a `CHECKPOINT_COVERAGE_CAVEAT` — Bash/background-subagent edits are structurally untracked), `sandbox_config` (read-only passthrough of the `sandbox` settings key, no assumed schema) — plus one SQLite-backed index (`app/db/connection.py`). `frontend/` (Vite/React/TS) has a working panel shell (Zustand nav + TanStack Query) with eight functional panels: Configuration Manager (read-only), MCP Hub (full CRUD + reachability test), Library & Organization (folder/tag/bookmark), Token & Cost Dashboard (stat tiles + SVG bar chart, dataviz-skill categorical palette), Canvas Pacchetti (React Flow node graph → save/load/activate/deactivate/preview-diff packages), Live Activity Monitor (WS session list + on-demand tool-use drilldown), Comparator (static diff + isolated/combination historical modes, plus a SessionStart-hook install/uninstall toggle), Estensioni Filesystem (Auto Memory / Rules Inspector / Checkpoint Viewer / Sandboxing / Output Styles as five sub-tabs of one panel, matching Fase 5's own "tutte read-mostly" scope — no editing endpoints). Fase 6 onward (import/export & marketplace, multi-agent monitor) is not yet built — see [IMPLEMENTATION_PLAN.md](docs/planning/IMPLEMENTATION_PLAN.md) for what's next, including the deferred-risk table (currently: missing CORS/Origin validation on mutating endpoints, a timestamp-string-comparison edge case in `telemetry_reader.summary`, and a narrow race window in the global-package-singleton invariant under concurrent activations).

### Common commands

Backend (from `backend/`, via `uv`):
```
uv run pytest -q                              # tests
uv run pytest -q --cov=app --cov-report=term-missing  # tests + coverage (must stay >=80%)
uv run pytest tests/config_reader -q          # single module's tests
uv run ruff check .                           # lint
uv run black .                                # format
```

Frontend (from `frontend/`, via `npm`):
```
npm run dev            # vite dev server (proxies /health, /system/* to backend on :8000)
npm run build           # tsc -b && vite build -> dist/, served by the backend
npm run lint             # eslint
npm run format            # prettier --write
```

Whole app: `./start.sh` from the repo root — builds the frontend if `frontend/dist` is missing, launches the backend (which also serves the built frontend), opens the browser, and blocks until the backend exits (the UI's "Spegni" button calls `POST /system/shutdown`, which terminates the process).

### Backend module layout

Each module under `backend/app/` has a matching test package under `backend/tests/` (e.g. `app/config_reader/` ↔ `tests/config_reader/`). Tests never touch the developer's real `~/.claude.json`/`~/.claude/` — they use `tmp_path` fixtures and, for FastAPI routes, override the path/DB dependencies declared in `app/api/dependencies.py` (`get_claude_json_path`, `get_global_settings_path`, `get_claude_home_path`, `get_db_connection`) via `app.dependency_overrides`. `app/db/connection.py`'s SQLite connection is opened with `check_same_thread=False` because FastAPI runs sync routes in a threadpool — safe here since this is a single-user local desktop app with one SQLite file, not a concurrent multi-writer service.

A known, deliberately-replicated Claude Code quirk: `compute_effective_permissions` in `app/config_reader/__init__.py` does **not** implement the documented "permissions merge across scopes" behavior for `settings.local.json` — it replicates the real, buggy behavior where local settings *replace* (not append to) the merged user+project permission lists, per-rule-type. See the reference doc cited below before changing this function.

A security-relevant design constraint in `package_registry`/`activation_engine`: canvas nodes of type skill/agent/command are never trusted with a client-supplied filesystem path. `POST /packages` resolves them server-side via `library_item_id` against `library_registry.scan_library()`'s own catalog, and `package_id`/path-derived node names are validated against a safe-slug pattern (`_validate_safe_identifier`) before ever touching the filesystem. Do not reintroduce a raw `source_path` field on the API surface — that was a real path-traversal/arbitrary-file-copy vulnerability caught in Fase 3 code review before being fixed.

## What this project is

A **local web app** ("Claude Code Control Plane") for managing, configuring, and visually observing a local Claude Code environment: global/project configuration, skills/agents/commands/output-styles, MCP servers, reusable "packages" (bundles of skills+agents+MCP+rules+prompts composed on a node canvas), activity, and token/cost telemetry.

Explicit non-goals (do not drift toward these): not an IDE (no source editor, no running Claude Code sessions inside the app), not a native app (no Tauri/Electron — pure local web app served over `http://localhost`), not a Claude Code plugin (no `.claude-plugin/` packaging or marketplace registration — it reads/writes the real files Claude Code itself uses), not an always-on daemon (manual start, shutdown via an in-app button), not integrated with the claude.ai account (filesystem-only scope; Routines/Artifacts/cloud Analytics/Remote Control are out of scope).

## Documentation map — read before implementing anything

- **[DESIGN.md](DESIGN.md)** — product goal, requirements, and the architectural decisions from the grilling session (source of truth for *why*).
- **[docs/planning/README.md](docs/planning/README.md)** — index of the planning docs below.
  - **[docs/planning/ARCHITECTURE.md](docs/planning/ARCHITECTURE.md)** — stack, backend module breakdown (one responsibility per module), SQLite schema, API contract, proposed repo layout.
  - **[docs/planning/IMPLEMENTATION_PLAN.md](docs/planning/IMPLEMENTATION_PLAN.md)** — the 8 sequential phases (Fase 0–7) with Definition of Done per phase, cross-cutting risks.
  - **[docs/planning/TASKS.md](docs/planning/TASKS.md)** — granular, dependency-ordered task list per phase, TDD-first (mark `[x]` only when tests are green).
- **[docs/claude-code-reference/](docs/claude-code-reference/)** — verified-from-primary-sources reference on Claude Code itself (skills/agents/commands, hooks/MCP/permissions, plugins/marketplace/config, full docs coverage map). **Consult this before writing any code against a Claude Code surface** (hook format, plugin schema, permission syntax, transcript format) — do not rely on prior/assumed knowledge, which may be stale.
- **[docs/](docs/)** — supporting research (activity-control mechanisms, interactive UI frameworks, community tooling landscape).

## Architecture (Fase 0–4 built; rest as planned)

Stack: **Python 3.12 + FastAPI** backend (serves REST + WebSocket + the built frontend) and **React (Vite) + TypeScript** frontend, with **React Flow** for the node canvas, **Zustand** for client state, **TanStack Query** for server state. Storage: a user-level SQLite index (`~/.claude-control-plane/index.sqlite`) for indexing/logging only — actual package content lives on the filesystem, either inside the project (`.claude-control-plane/packages/<id>/`) or under the user home for global packages (`~/.claude-control-plane/global-packages/<id>/`). Full rationale and schema in [ARCHITECTURE.md](docs/planning/ARCHITECTURE.md).

The backend is organized as one module per responsibility (`config_reader`, `mcp_manager`, `library_registry`, `project_discovery`, `package_registry`, `activation_engine`, `telemetry_reader`, `activity_monitor`, `hooks_installer`, `comparator`, `memory_reader`, `rules_inspector`, `checkpoint_reader`, `sandbox_config`, `sanitizer`, `db`, `api`) — see the module table in ARCHITECTURE.md for what each reads/writes and which real Claude Code file it depends on (`~/.claude.json`, `~/.claude/settings.json`, `.mcp.json`, `.claude/skills|agents|commands|output-styles/`, `~/.claude/projects/**/*.jsonl`, `~/.claude/sessions/*.json`, etc.).

Two invariants that recur across the design and matter for any future change touching activation or config:
- **Global scope allows exactly one active package at a time**; **project scope allows N active packages simultaneously**. This asymmetry is intentional (global = base environment, project = composable).
- **Every write to real Claude Code folders is merge/append with a diff preview, never a silent overwrite**, and every removal is checked against a manifest (`written_files` table, content hash) of what the Control Plane itself wrote — so a file the user edited manually after activation is never deleted on deactivation. `settings.local.json` is a known non-merge special case (it overwrites, not merges, global permissions) and must be handled explicitly, never assumed to merge.

## Execution rules for implementing the plan

Phases in IMPLEMENTATION_PLAN.md are **sequential**; tasks within a phase in TASKS.md are dependency-ordered. TDD is mandatory per the global rules already in effect (`~/.claude/rules/ecc/common/`): write the test first with fixtures, **never** against the developer's real `~/.claude.json`/`~/.claude/` files. At the end of each phase: run tests, verify that phase's Definition of Done in IMPLEMENTATION_PLAN.md, then code review, then commit — before starting the next phase.
