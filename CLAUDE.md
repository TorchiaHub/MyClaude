# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

This repo is **pre-implementation**: only planning documentation and imported reference skills exist (`docs/`, `DESIGN.md`, `.claude/skills/`). There is no `backend/` or `frontend/` yet, no build system, no tests, no lint config — so there are no build/lint/test commands to document until Fase 0 of the implementation plan is executed. Once that scaffolding exists, this file should be updated with the real commands (expected: `pytest` for backend, `npm`/`vite` for frontend, a `start.sh` launcher — see roadmap below).

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

## Architecture (as planned — not yet built)

Stack: **Python 3.12 + FastAPI** backend (serves REST + WebSocket + the built frontend) and **React (Vite) + TypeScript** frontend, with **React Flow** for the node canvas, **Zustand** for client state, **TanStack Query** for server state. Storage: a user-level SQLite index (`~/.claude-control-plane/index.sqlite`) for indexing/logging only — actual package content lives on the filesystem, either inside the project (`.claude-control-plane/packages/<id>/`) or under the user home for global packages (`~/.claude-control-plane/global-packages/<id>/`). Full rationale and schema in [ARCHITECTURE.md](docs/planning/ARCHITECTURE.md).

The backend is organized as one module per responsibility (`config_reader`, `mcp_manager`, `library_registry`, `project_discovery`, `package_registry`, `activation_engine`, `telemetry_reader`, `activity_monitor`, `hooks_installer`, `comparator`, `memory_reader`, `rules_inspector`, `checkpoint_reader`, `sandbox_config`, `sanitizer`, `db`, `api`) — see the module table in ARCHITECTURE.md for what each reads/writes and which real Claude Code file it depends on (`~/.claude.json`, `~/.claude/settings.json`, `.mcp.json`, `.claude/skills|agents|commands|output-styles/`, `~/.claude/projects/**/*.jsonl`, `~/.claude/sessions/*.json`, etc.).

Two invariants that recur across the design and matter for any future change touching activation or config:
- **Global scope allows exactly one active package at a time**; **project scope allows N active packages simultaneously**. This asymmetry is intentional (global = base environment, project = composable).
- **Every write to real Claude Code folders is merge/append with a diff preview, never a silent overwrite**, and every removal is checked against a manifest (`written_files` table, content hash) of what the Control Plane itself wrote — so a file the user edited manually after activation is never deleted on deactivation. `settings.local.json` is a known non-merge special case (it overwrites, not merges, global permissions) and must be handled explicitly, never assumed to merge.

## Execution rules for implementing the plan

Phases in IMPLEMENTATION_PLAN.md are **sequential**; tasks within a phase in TASKS.md are dependency-ordered. TDD is mandatory per the global rules already in effect (`~/.claude/rules/ecc/common/`): write the test first with fixtures, **never** against the developer's real `~/.claude.json`/`~/.claude/` files. At the end of each phase: run tests, verify that phase's Definition of Done in IMPLEMENTATION_PLAN.md, then code review, then commit — before starting the next phase.
