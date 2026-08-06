# Task list — Claude Code Control Plane

[← README pianificazione](./README.md) · [Architettura](./ARCHITECTURE.md) · [Piano](./IMPLEMENTATION_PLAN.md)

Task sequenziali per fase (vedi [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) per Definition of Done e rischi). Test prima, poi implementazione minima (TDD). Prima di lavorare contro una superficie di Claude Code, consultare [docs/claude-code-reference/](../claude-code-reference/). Segna `[x]` solo a test verdi.

## Fase 0 — Bootstrap

- [ ] Init repository git, `.gitignore` (Python + Node), struttura cartelle `backend/`, `frontend/`, `docs/`
- [ ] Backend: ambiente Python (uv/poetry), FastAPI + pytest, `GET /health`, `POST /system/shutdown`
- [ ] Frontend: scaffold Vite + React + TypeScript, build statica
- [ ] Backend serve la build statica del frontend su `http://localhost:<porta>`
- [ ] Script di avvio (`start.sh`) che lancia il backend e apre il browser
- [ ] Verifica: il pulsante "spegni" in UI chiama `/system/shutdown` e termina il processo
- [ ] Setup lint/format backend (ruff/black) e frontend (eslint/prettier)

## Fase 1 — Core Backend

- [ ] `config_reader`: parsing `~/.claude.json`/`~/.claude/settings.json` (fixture, mai file reali) — test prima
- [ ] `config_reader`: parsing `.mcp.json` di progetto — test prima
- [ ] `config_reader`: gestione esplicita `settings.local.json` non-merge sui permessi — test che riproduce il caso
- [ ] `mcp_manager`: list/add/remove server MCP (globale + progetto) — test prima
- [ ] `mcp_manager`: test di raggiungibilità di un server MCP configurato
- [ ] `library_registry`: scansione skill/agenti/comandi (nome, descrizione, categoria/tag da frontmatter) — test prima
- [ ] `library_registry`: scansione output style — test prima
- [ ] `library_registry`: indice cartelle/tag/bookmark in SQLite (CRUD) — test prima
- [ ] `project_discovery`: auto-scan `~/.claude/projects/` — test prima con fixture directory
- [ ] `project_discovery`: registrazione manuale di una cartella progetto — test prima
- [ ] Router FastAPI: `/config/global`, `/config/project`, `/mcp/servers`, `/library`, `/projects` — integration test per ciascuno
- [ ] Code review prima di passare alla Fase 2

## Fase 2 — UI Base + Token & Cost Dashboard

- [ ] Layout frontend: shell con navigazione tra pannelli
- [ ] Pannello Configuration Manager: vista + form, collegato a `/config/*`
- [ ] Pannello MCP Hub: elenco, add/remove/test
- [ ] Pannello Library & Organization: albero cartelle, filtro tag multi-select, toggle bookmark, anteprima contenuto (sola lettura)
- [ ] `telemetry_reader`: parsing incrementale `.jsonl` per token/costo per turno — test prima con fixture transcript minimale
- [ ] `telemetry_reader`: lettura cumulativi da `~/.claude.json → projects.*` — test prima
- [ ] Endpoint `/telemetry/summary` (filtri progetto/pacchetto/periodo) — integration test
- [ ] Pannello Token & Cost Dashboard: grafici trend costo, breakdown per progetto/pacchetto
- [ ] Code review prima di passare alla Fase 3

## Fase 3 — Canvas, Activation Engine & Live Activity Monitor

- [ ] Setup React Flow, tipi di nodo custom: skill / agente / comando / MCP / regola / prompt
- [ ] `package_registry`: CRUD pacchetto, scope `global`/`project`, contenuto su filesystem + indice SQLite — test prima
- [ ] Canvas: salvataggio → pacchetto; caricamento pacchetto esistente → ripopolamento canvas
- [ ] `activation_engine`: merge/append con diff preview — test prima (incl. caso file già esistente con contenuto diverso)
- [ ] `activation_engine`: scrittura manifest `written_files` (hash) ad ogni attivazione — test prima
- [ ] `activation_engine`: rimozione su disattivazione, verificata contro manifest — test prima del caso critico: file modificato manualmente dall'utente **non** viene rimosso
- [ ] `activation_engine`: regola "una recipe globale attiva" (disattiva la precedente) vs "N pacchetti locali attivi" — test prima per entrambi i rami
- [ ] Endpoint `/packages`, `/packages/{id}/activate`, `/packages/{id}/deactivate` — integration test
- [ ] `activity_monitor` livello sessione: poll `~/.claude/sessions/*.json`, WS `/activity/live` — test prima con fixture directory sessioni
- [ ] Pannello Live Monitor: lista sessioni attive, stato busy/idle, aggiornamento realtime
- [ ] `activity_monitor` drill-down: tail `.jsonl` sessione + subagent, eventi `tool_use`/`Task` — test prima, incluso il **degrado controllato** su formato non riconosciuto
- [ ] Pannello Live Monitor: espansione per sessione con "cosa sta facendo ora"
- [ ] Code review prima di passare alla Fase 4

## Fase 4 — Workflow Comparator

- [ ] `hooks_installer`: append di una entry a `settings.json → hooks.SessionStart` (array, non sovrascrittura) — test prima su file di fixture, mai quello reale
- [ ] Endpoint che riceve la notifica `SessionStart` e scrive `session_started` (session_id, cwd, timestamp) — test prima
- [ ] `comparator`: diff statico tra due pacchetti (`skills_required`, `mcp_dependencies`, `agents_required`, `instructions`) — test prima
- [ ] `comparator`: aggregazione storica modalità "combinazione attiva nel tempo" (incrocio `activation_log` + `session_started` + `telemetry_cache`) — test prima
- [ ] `comparator`: aggregazione storica modalità "pacchetto isolato" — test prima
- [ ] Endpoint `/packages/compare?a=&b=&mode=` — integration test
- [ ] Pannello Comparator: selezione due pacchetti (+ suggerimento da tag "alternativi"), vista diff + metriche affiancate per entrambe le modalità
- [ ] Code review prima di passare alla Fase 5

## Fase 5 — Estensioni filesystem (batch)

- [ ] `memory_reader`: lettura `MEMORY.md` + topic file, storia `modified` — test prima
- [ ] `rules_inspector`: parsing `.claude/rules/*.md` e frontmatter `paths:` — test prima
- [ ] `checkpoint_reader`: estrazione timeline checkpoint dal transcript — test prima, incluso segnalare cosa non è coperto (Bash, subagent)
- [ ] `sandbox_config`: lettura/scrittura config sandboxing — test prima
- [ ] `library_registry`: estensione a output style già coperta in Fase 1 — verifica pannello dedicato
- [ ] Endpoint `/memory/{project}`, `/rules/{project}`, `/checkpoints/{session_id}`, `/sandbox/config`, `/output-styles` — integration test
- [ ] Pannelli: Auto Memory Viewer, Rules Inspector, Checkpoint Viewer, Sandboxing Editor, Output Styles Manager
- [ ] Code review prima di passare alla Fase 6

## Fase 6 — Import/Export & Marketplace

- [ ] `sanitizer`: rimozione chiavi API/percorsi assoluti/cache locale — test che asserisce esplicitamente l'assenza di questi campi
- [ ] Endpoint `/packages/{id}/export`
- [ ] Wizard import: rilevamento skill/MCP mancanti localmente rispetto al pacchetto importato — test prima
- [ ] Endpoint `/packages/import` con mapping delle dipendenze esterne
- [ ] Pannello Import/Export: UI del wizard
- [ ] Code review + verifica end-to-end (export → import su cartella pulita di test → nessun dato sensibile presente)

## Fase 7 — Multi-Agent Monitor *(design dedicato quando si arriva qui)*

- [ ] Sessione di design specifica: schema dati per agent view/team/dynamic workflow, UI multi-sessione
- [ ] Task successivi da definire a valle di quel design

## Non pianificare (fuori scope)

- Editor/IDE per codice sorgente
- App nativa, packaging come plugin Claude Code, processo permanente
- Integrazione account claude.ai (OAuth, Routines, Artifacts, Analytics, Remote Control)
- Enforcement/blocco attivo su budget token
- OpenTelemetry come fonte primaria di telemetria
