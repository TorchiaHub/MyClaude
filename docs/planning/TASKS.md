# Task list — Claude Code Control Plane

[← README pianificazione](./README.md) · [Architettura](./ARCHITECTURE.md) · [Piano](./IMPLEMENTATION_PLAN.md)

Task sequenziali per fase (vedi [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) per Definition of Done e rischi). Test prima, poi implementazione minima (TDD). Prima di lavorare contro una superficie di Claude Code, consultare [docs/claude-code-reference/](../claude-code-reference/). Segna `[x]` solo a test verdi.

## Fase 0 — Bootstrap

- [x] Init repository git, `.gitignore` (Python + Node), struttura cartelle `backend/`, `frontend/`, `docs/`
- [x] Backend: ambiente Python (uv/poetry), FastAPI + pytest, `GET /health`, `POST /system/shutdown`
- [x] Frontend: scaffold Vite + React + TypeScript, build statica
- [x] Backend serve la build statica del frontend su `http://localhost:<porta>`
- [x] Script di avvio (`start.sh`) che lancia il backend e apre il browser
- [x] Verifica: il pulsante "spegni" in UI chiama `/system/shutdown` e termina il processo
- [x] Setup lint/format backend (ruff/black) e frontend (eslint/prettier)

## Fase 1 — Core Backend

- [x] `config_reader`: parsing `~/.claude.json`/`~/.claude/settings.json` (fixture, mai file reali) — test prima
- [x] `config_reader`: parsing `.mcp.json` di progetto — test prima
- [x] `config_reader`: gestione esplicita `settings.local.json` non-merge sui permessi — test che riproduce il caso
- [x] `mcp_manager`: list/add/remove server MCP (globale + progetto) — test prima
- [x] `mcp_manager`: test di raggiungibilità di un server MCP configurato
- [x] `library_registry`: scansione skill/agenti/comandi (nome, descrizione, categoria/tag da frontmatter) — test prima
- [x] `library_registry`: scansione output style — test prima
- [x] `library_registry`: indice cartelle/tag/bookmark in SQLite (CRUD) — test prima
- [x] `project_discovery`: auto-scan `~/.claude/projects/` — test prima con fixture directory
- [x] `project_discovery`: registrazione manuale di una cartella progetto — test prima
- [x] Router FastAPI: `/config/global`, `/config/project`, `/mcp/servers`, `/library`, `/projects` — integration test per ciascuno
- [x] Code review prima di passare alla Fase 2

## Fase 2 — UI Base + Token & Cost Dashboard

- [x] Layout frontend: shell con navigazione tra pannelli
- [x] Pannello Configuration Manager: vista, collegato a `/config/*` (solo lettura in questa fase — form editabile aggiunto nell'addendum post-Fase 6, vedi sotto)
- [x] Pannello MCP Hub: elenco, add/remove/test
- [x] Pannello Library & Organization: albero cartelle, filtro tag multi-select, toggle bookmark, anteprima contenuto (sola lettura)
- [x] `telemetry_reader`: parsing incrementale `.jsonl` per token/costo per turno — test prima con fixture transcript minimale
- [x] `telemetry_reader`: lettura cumulativi da `~/.claude.json → projects.*` — test prima
- [x] Endpoint `/telemetry/summary` (filtri progetto/pacchetto/periodo) — integration test
- [x] Pannello Token & Cost Dashboard: grafici trend costo, breakdown per progetto/pacchetto
- [x] Code review prima di passare alla Fase 3

## Fase 3 — Canvas, Activation Engine & Live Activity Monitor

- [x] Setup React Flow, tipi di nodo custom: skill / agente / comando / MCP / regola / prompt
- [x] `package_registry`: CRUD pacchetto, scope `global`/`project`, contenuto su filesystem + indice SQLite — test prima
- [x] Canvas: salvataggio → pacchetto; caricamento pacchetto esistente → ripopolamento canvas
- [x] `activation_engine`: merge/append con diff preview — test prima (incl. caso file già esistente con contenuto diverso)
- [x] `activation_engine`: scrittura manifest `written_files` (hash) ad ogni attivazione — test prima
- [x] `activation_engine`: rimozione su disattivazione, verificata contro manifest — test prima del caso critico: file modificato manualmente dall'utente **non** viene rimosso
- [x] `activation_engine`: regola "una recipe globale attiva" (disattiva la precedente) vs "N pacchetti locali attivi" — test prima per entrambi i rami
- [x] Endpoint `/packages`, `/packages/{id}/activate`, `/packages/{id}/deactivate` — integration test
- [x] `activity_monitor` livello sessione: poll `~/.claude/sessions/*.json`, WS `/activity/live` — test prima con fixture directory sessioni
- [x] Pannello Live Monitor: lista sessioni attive, stato busy/idle, aggiornamento realtime
- [x] `activity_monitor` drill-down: tail `.jsonl` sessione + subagent, eventi `tool_use`/`Task` — test prima, incluso il **degrado controllato** su formato non riconosciuto
- [x] Pannello Live Monitor: espansione per sessione con "cosa sta facendo ora"
- [x] Code review prima di passare alla Fase 4

## Fase 4 — Workflow Comparator

- [x] `hooks_installer`: append di una entry a `settings.json → hooks.SessionStart` (array, non sovrascrittura) — test prima su file di fixture, mai quello reale
- [x] Endpoint che riceve la notifica `SessionStart` e scrive `session_started` (session_id, cwd, timestamp) — test prima
- [x] `comparator`: diff statico tra due pacchetti (`skills_required`, `mcp_dependencies`, `agents_required`, `instructions`) — test prima
- [x] `comparator`: aggregazione storica modalità "combinazione attiva nel tempo" (incrocio `activation_log` + `session_started` + `telemetry_cache`) — test prima
- [x] `comparator`: aggregazione storica modalità "pacchetto isolato" — test prima
- [x] Endpoint `/packages/compare?a=&b=&mode=` — integration test
- [x] Pannello Comparator: selezione due pacchetti (+ suggerimento da tag "alternativi"), vista diff + metriche affiancate per entrambe le modalità
- [x] Code review prima di passare alla Fase 5

## Fase 5 — Estensioni filesystem (batch)

- [x] `memory_reader`: lettura `MEMORY.md` + topic file, storia `modified` — test prima
- [x] `rules_inspector`: parsing `.claude/rules/*.md` e frontmatter `paths:` — test prima
- [x] `checkpoint_reader`: estrazione timeline checkpoint dal transcript — test prima, incluso segnalare cosa non è coperto (Bash, subagent)
- [x] `sandbox_config`: lettura/scrittura config sandboxing — test prima
- [x] `library_registry`: estensione a output style già coperta in Fase 1 — verifica pannello dedicato
- [x] Endpoint `/memory/{project}`, `/rules/{project}`, `/checkpoints/{session_id}`, `/sandbox/config`, `/output-styles` — integration test
- [x] Pannelli: Auto Memory Viewer, Rules Inspector, Checkpoint Viewer, Sandboxing Editor, Output Styles Manager
- [x] Code review prima di passare alla Fase 6

## Fase 6 — Import/Export & Marketplace

- [x] `sanitizer`: rimozione chiavi API/percorsi assoluti/cache locale — test che asserisce esplicitamente l'assenza di questi campi
- [x] Endpoint `/packages/{id}/export`
- [x] Wizard import: rilevamento skill/MCP mancanti localmente rispetto al pacchetto importato — test prima
- [x] Endpoint `/packages/import` con mapping delle dipendenze esterne
- [x] Pannello Import/Export: UI del wizard
- [x] Code review + verifica end-to-end (export → import su cartella pulita di test → nessun dato sensibile presente)

## Addendum post-Fase 6 — Configuration Manager editabile & Claude Globale

Non previsto nello scope originale di alcuna fase pianificata — vedi [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md#addendum-post-fase-6--configuration-manager-editabile--claude-globale).

- [x] `PUT /config/global/permissions`, `PUT /config/project/permissions`: move/add/remove regole allow/ask/deny — test prima
- [x] Pannello Configuration Manager: form editabile per le regole di permesso (dual view globale/progetto)
- [x] `home_browser`: list/preview/rename/move/delete su tutto `~/.claude/`, con guard robusto su root-escape (path risolti, non stringhe grezze) — test prima incl. caso simlink e forme equivalenti (`"./"`, `"././"`)
- [x] `claude_home_graph`: grafo nodi/archi reali (CLAUDE.md, settings, skill/agenti/comandi/output-style, regole, edge strutturali skill-annidate e hook→script) — test prima
- [x] Router `/claude-home/*`: graph, tree, file, rename, move, entry (delete) — integration test per ciascuno
- [x] Pannello Claude Globale: canvas React Flow read-only (grafo filtrato ai nodi connessi) + folder browser lazy-loaded con conferma nativa obbligatoria prima di ogni delete
- [x] Code review con focus sicurezza (path traversal/root-escape) — CRITICAL trovato e corretto prima del merge

## Fase 7 — Multi-Agent Monitor *(design dedicato quando si arriva qui)*

- [ ] Sessione di design specifica: schema dati per agent view/team/dynamic workflow, UI multi-sessione
- [ ] Task successivi da definire a valle di quel design

## Non pianificare (fuori scope)

- Editor/IDE per codice sorgente
- App nativa, packaging come plugin Claude Code, processo permanente
- Integrazione account claude.ai (OAuth, Routines, Artifacts, Analytics, Remote Control)
- Enforcement/blocco attivo su budget token
- OpenTelemetry come fonte primaria di telemetria
