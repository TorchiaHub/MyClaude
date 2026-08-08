# Architettura — Claude Code Control Plane

[← README pianificazione](./README.md)

## Perimetro

Web app locale per gestire visivamente ciò che Claude Code usa e fa: configurazione, skill, agenti, comandi, output style, server MCP, pacchetti/workflow, attività, costi. **Non** un IDE, **non** un'app nativa, **non** un plugin Claude Code, **non** un processo permanente, **non** integrata con l'account claude.ai (filesystem-only). Vedi [DESIGN.md §1](../../DESIGN.md#1-obiettivo-e-scopo-del-progetto) per i non-goal completi.

## Stack

| Livello | Scelta | Motivazione |
|---|---|---|
| Backend | **Python 3.12 + FastAPI** | Accesso filesystem, parsing, API REST + WS; serve anche la build statica del frontend |
| Frontend | **React (Vite) + TypeScript** | Ecosistema maturo per i pannelli previsti |
| Canvas a nodi | **React Flow (xyflow)** | Copre drag/zoom/pan/selection/persistence; nessun bisogno del motore dataflow di Rete.js |
| State (client) | **Zustand** | Nessun boilerplate/provider, adatto a più pannelli indipendenti |
| State (server/API) | **TanStack Query** | Caching/refetch per i dati letti dal backend |
| Comunicazione realtime | **WebSocket** dal backend + event bus lato frontend | Disaccoppia i pannelli tra loro |
| Avvio/arresto | Script shell di avvio a comando + endpoint `/system/shutdown` richiamato dal pulsante "spegni" in UI | Nessun processo permanente, nessun autostart di sistema |
| Storage indice/cache | **SQLite** utente (`~/.claude-control-plane/index.sqlite`) | Solo indice/organizzazione/log/cache — mai contenuto |
| Storage contenuto pacchetti | Cartella dentro il progetto (`.claude-control-plane/packages/<id>/`) per lo scope `project`; cartella utente (`~/.claude-control-plane/global-packages/<id>/`) per lo scope `global` | Portabilità/leggerezza del progetto, coerente con "pacchetti esportabili nel progetto" |

**Cosa NON c'è, deliberatamente:** Tauri/Electron (web app pura), OAuth verso claude.ai (filesystem-only), packaging `.claude-plugin/` (l'app non è un plugin), demone always-on/systemd service (avvio manuale).

## Componenti backend

Un modulo per responsabilità, file piccoli e focalizzati (200–400 righe tipiche):

| Modulo | Responsabilità | Fonte dati |
|---|---|---|
| `config_reader` | Legge/scrive `~/.claude.json`, `~/.claude/settings.json`, `.mcp.json` di progetto; gestisce il caso non-merge di `settings.local.json` | Filesystem |
| `mcp_manager` | Lista, test, add/remove server MCP (globali e per-progetto) | `mcpServers` |
| `library_registry` | Catalogo skill/agenti/comandi/output style: scansione, metadati, indice cartelle/tag/bookmark | `.claude/skills/`, `.claude/agents/`, `.claude/commands/`, `.claude/output-styles/` |
| `project_discovery` | Auto-scan `~/.claude/projects/` + registrazione manuale di cartelle progetto | `~/.claude/projects/` |
| `package_registry` | CRUD pacchetti (schema DESIGN.md §5), scope `global`/`project`, persistenza contenuto su filesystem + indice in SQLite | File pacchetto + SQLite `packages` |
| `activation_engine` | Attiva/disattiva un pacchetto: merge/append con diff preview, scrittura manifest, rimozione verificata su manifest; applica la regola "una sola recipe globale attiva" vs "N pacchetti locali attivi" | Cartelle reali Claude Code + SQLite `activation_log` |
| `telemetry_reader` | Parsing incrementale `.jsonl` per token/costi; lettura cumulativi da `.claude.json → projects.*` | `~/.claude/projects/*/*.jsonl`, `~/.claude.json` |
| `activity_monitor` | Poll `~/.claude/sessions/*.json` (livello sessione) + tail `.jsonl`/subagent per drill-down tool/skill/agente attivo | `~/.claude/sessions/*.json`, transcript |
| `hooks_installer` | Aggiunge/rimuove una entry nell'array `~/.claude/settings.json → hooks.SessionStart` per notificare il backend dell'avvio sessione (append sicuro, **non** un plugin) | `~/.claude/settings.json → hooks` |
| `comparator` | Diff statico tra pacchetti + aggregazione storica per finestra temporale (combinazione attiva vs pacchetto isolato) da `activation_log` | `package_registry` + `activation_log` + `telemetry_cache` |
| `memory_reader` | Lettura/audit `MEMORY.md` + topic file | `~/.claude/projects/<project>/memory/` |
| `rules_inspector` | Parsing `.claude/rules/*.md` e frontmatter `paths:` | `.claude/rules/` |
| `checkpoint_reader` | Estrazione timeline checkpoint dal transcript sessione | `.jsonl` sessione |
| `sandbox_config` | Lettura/scrittura config sandboxing (allowlist filesystem/rete) | `~/.claude/settings.json` (chiavi sandbox) |
| `multi_agent_monitor` *(fase successiva)* | Stato agent view/team/dynamic workflow | `~/.claude/jobs/`, mailbox JSON, `.claude/worktrees/` |
| `sanitizer` | Rimozione segreti/percorsi/cache locale in fase di export | — |
| `home_browser` | Operazioni file (list/preview/rename/move/delete) su **tutto** `~/.claude/`, senza esclusioni — scelta di scope deliberata. Unico invariante: `root` non è mai escapable/cancellabile (`_resolve_safe_path`, confronto su path *risolti*, robusto a symlink e forme equivalenti come `"./"`) | `~/.claude/` (intero albero) |
| `claude_home_graph` | Costruisce il grafo nodi/archi dell'ambiente globale (CLAUDE.md, settings.json, ogni skill/agente/comando/output-style da `library_registry`, ogni regola da `rules_inspector`) con archi strutturali reali (skill annidate, hook→script) — nessun parsing free-text di CLAUDE.md | `~/.claude/` + `library_registry` + `rules_inspector` |
| `db` | Modelli e accesso SQLite | SQLite |
| `api` | Router FastAPI che espone i moduli sopra + serve la build frontend | — |
| `origin_guard` *(modulo flat, non package)* | Middleware globale: rifiuta `POST`/`PUT`/`PATCH`/`DELETE` il cui header `Origin` non corrisponde a scheme/host/porta della request; richieste senza `Origin` (curl, hook) passano invariate | — |

**Nota sul parsing dei transcript:** interfaccia isolata e sostituibile (vedi DESIGN.md §3) — resta parsing diretto per l'MVP, non OTel, per non introdurre un collector sempre attivo.

## Componenti frontend

Nav key effettiva in `frontend/src/store/navigationStore.ts` tra parentesi. 10 pannelli registrati (non 14: "Local Package Manager" non è un pannello separato — la gestione pacchetti di progetto/globale vive nello stesso Canvas del Visual Workflow Canvas; Auto Memory/Rules/Checkpoint/Sandboxing/Output Styles sono 5 sub-tab di un unico pannello "Estensioni Filesystem", non 5 pannelli distinti; Multi-Agent Monitor non è ancora costruito, Fase 7).

| Pannello (nav key) | Contenuto | Editing? |
|---|---|---|
| Configuration Manager (`config`) | Config globale + progetto (permessi allow/ask/deny) | Sì — `PUT /config/global\|project/permissions` |
| MCP Hub (`mcp`) | Elenco, test, attivazione/disattivazione server MCP | Sì (form + test raggiungibilità) |
| Library & Organization (`library`) | Catalogo skill/agenti/comandi/output style; albero cartelle + filtro tag + preferiti | Solo bookmark (`POST /library/bookmark`) |
| Token & Cost Dashboard (`dashboard`) | Grafici costo/token per sessione/progetto/pacchetto/periodo | No (read-only) |
| Canvas Pacchetti (`canvas`) | Composizione nodi → pacchetto, scope globale (singolo attivo) e progetto (N attivi); crea/attiva/disattiva/preview-diff | Sì (canvas + attivazione) |
| Live Activity Monitor (`activity`) | Sessioni attive (WS `/activity/live`) + drill-down skill/agente/tool su richiesta | No (read-only) |
| Multi-Agent Monitor *(Fase 7, non costruito)* | Agent view/team/dynamic workflow | No (read-only) |
| Comparator (`comparator`) | Diff statico + confronto storico (combinazione / isolato); toggle install/uninstall hook SessionStart | Diff/metriche read-only; mutazione solo sull'hook |
| Estensioni Filesystem (`filesystem`) | 5 sub-tab: Auto Memory, Rules Inspector, Checkpoint Viewer, Sandboxing, Output Styles | No (read-only — nessun endpoint di scrittura, a differenza del design originale) |
| Import/Export (`import-export`) | Export sanitizzato per download / import file con report dipendenze mancanti | Sì (import è `POST`; export è `GET` download) |
| Claude Globale (`claude-global`) | 2 sub-tab: canvas React Flow read-only del grafo `claude_home_graph` (filtrato ai nodi connessi) + folder browser sull'intero `~/.claude/` | Sì — rename/move/delete via `home_browser`, con conferma nativa obbligatoria prima di ogni delete |

## Comunicazione tra pannelli

Event bus alimentato dal canale WebSocket del backend. Eventi tipizzati minimi: `session.status_changed`, `session.tool_activity`, `package.activated`, `package.deactivated`, `package.saved`, `mcp.status_changed`. Ogni pannello si iscrive solo agli eventi che gli servono (pattern pub/sub, vedi [ricerca UI](../ricerca-ui-interattive-framework.md) §4).

## Storage — schema minimo

```sql
CREATE TABLE packages (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  scope TEXT NOT NULL CHECK (scope IN ('global', 'project')),
  project_path TEXT,              -- NULL se scope = 'global'
  content_path TEXT NOT NULL,     -- dove vive il contenuto canonico sul filesystem
  folder TEXT,                    -- collocazione primaria nella Library
  updated_at INTEGER NOT NULL
);

CREATE TABLE package_tags (
  package_id TEXT REFERENCES packages(id),
  tag TEXT NOT NULL,
  PRIMARY KEY (package_id, tag)
);

CREATE TABLE bookmarks (
  package_id TEXT PRIMARY KEY REFERENCES packages(id)
);

-- log, non stato corrente: necessario per il confronto storico per finestra temporale
CREATE TABLE activation_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  package_id TEXT REFERENCES packages(id),
  project_path TEXT,              -- NULL se scope = 'global'
  action TEXT NOT NULL CHECK (action IN ('activate', 'deactivate')),
  occurred_at INTEGER NOT NULL
);

-- correlazione sessione -> cwd, popolata dall'hook SessionStart
CREATE TABLE session_started (
  session_id TEXT PRIMARY KEY,
  cwd TEXT NOT NULL,
  started_at INTEGER NOT NULL
);

CREATE TABLE telemetry_cache (
  session_id TEXT PRIMARY KEY,
  tokens_in INTEGER NOT NULL,
  tokens_out INTEGER NOT NULL,
  cost_usd REAL NOT NULL,
  updated_at INTEGER NOT NULL
);

-- manifest di ciò che activation_engine ha scritto, per rimozione sicura
CREATE TABLE written_files (
  package_id TEXT REFERENCES packages(id),
  project_path TEXT,
  file_path TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  PRIMARY KEY (package_id, project_path, file_path)
);
```

Il Comparator ricostruisce "quali pacchetti erano attivi in un dato momento per un dato progetto" incrociando `activation_log` (eventi activate/deactivate nel tempo) con `session_started` (quando una sessione è iniziata, per quel `cwd`) e `telemetry_cache` (le sue metriche).

## Contratto API (stato reale — verificato su `backend/app/api/`)

| Endpoint | Metodo | Scopo |
|---|---|---|
| `/health` | GET | Health check |
| `/system/shutdown` | POST | Spegnimento del backend da UI |
| `/config/global` | GET | Configuration Manager — config globale |
| `/config/project?path=` | GET | Configuration Manager — config progetto |
| `/config/global/permissions` | PUT | Configuration Manager — riscrive allow/ask/deny globali |
| `/config/project/permissions?path=` | PUT | Configuration Manager — riscrive allow/ask/deny di progetto |
| `/mcp/servers` | GET/POST | MCP Hub — elenco, aggiunta |
| `/mcp/servers/{name}` | DELETE | MCP Hub — rimozione |
| `/mcp/servers/{name}/test` | POST | MCP Hub — test raggiungibilità |
| `/library` | GET | Library & Organization |
| `/library/bookmark` | POST | Library — toggle bookmark |
| `/projects` | GET/POST | Project discovery (auto-scan + aggiunta manuale) |
| `/telemetry/summary` | GET | Token & Cost Dashboard |
| `/packages` | GET/POST | Package registry — elenco, creazione |
| `/packages/{id}` | GET/DELETE | Package registry — dettaglio, cancellazione |
| `/packages/{id}/export` | GET | Import/Export — download sanitizzato |
| `/packages/{id}/preview-activation` | GET | Canvas — diff preview prima di attivare |
| `/packages/{id}/activate`, `/deactivate` | POST | Activation engine |
| `/packages/compare?a=&b=&mode=combination\|isolated` | GET | Workflow Comparator |
| `/packages/import` | POST | Import/Export — materializza bundle importato |
| `/activity/live` | WS | Live Activity Monitor — sessioni realtime |
| `/activity/sessions/{session_id}/drilldown` | GET | Live Activity Monitor — drill-down tool_use su richiesta |
| `/hooks/session-start/status` | GET | Comparator — stato installazione hook |
| `/hooks/session-start/install` | POST | Comparator — installa hook SessionStart |
| `/hooks/session-start/install` | DELETE | Comparator — disinstalla hook |
| `/hooks/session-start` | POST | Riceve la notifica dell'hook a runtime |
| `/memory?project_path=` | GET | Auto Memory Viewer (query param, non path param) |
| `/rules?project_path=` | GET | Rules Inspector (`project_path` opzionale) |
| `/checkpoints/{session_id}?cwd=` | GET | Checkpoint Viewer |
| `/sandbox/config` | GET | Sandboxing — sola lettura, nessun `PUT` implementato |
| `/output-styles?project_path=` | GET | Output Styles — sola lettura, nessun `POST` implementato |
| `/claude-home/graph` | GET | Claude Globale — grafo ambiente |
| `/claude-home/tree?path=` | GET | Claude Globale — folder browser |
| `/claude-home/file?path=` | GET | Claude Globale — anteprima file |
| `/claude-home/rename` | PATCH | Claude Globale — rinomina entry |
| `/claude-home/move` | PATCH | Claude Globale — sposta entry |
| `/claude-home/entry?path=` | DELETE | Claude Globale — cancella entry (conferma nativa lato UI) |

Nota: i router `filesystem_extensions` e `claude_home` non erano nel contratto API originale (bozza pre-Fase 5/6) — `filesystem_extensions` monta senza prefix (endpoint a radice `/memory`, `/rules`, ecc., non `/filesystem/*`), `claude_home` monta con prefix `/claude-home`. `Sandboxing Editor` e `Output Styles Manager` restano GET-only nonostante il design originale (§4 DESIGN.md) li descriva come editabili — coerente con la scelta di Fase 5 "tutte read-mostly" fatta durante l'implementazione.

## Layout repository proposto

```
/
├── DESIGN.md
├── docs/
│   ├── planning/             (questo set di documenti)
│   └── claude-code-reference/ (reference tecnico Claude Code)
├── backend/                  (FastAPI, un modulo per file come da tabella sopra)
│   ├── app/
│   │   ├── api/
│   │   ├── config_reader/
│   │   ├── mcp_manager/
│   │   ├── library_registry/
│   │   ├── project_discovery/
│   │   ├── package_registry/
│   │   ├── activation_engine/
│   │   ├── telemetry_reader/
│   │   ├── activity_monitor/
│   │   ├── hooks_installer/
│   │   ├── comparator/
│   │   ├── memory_reader/
│   │   ├── rules_inspector/
│   │   ├── checkpoint_reader/
│   │   ├── sandbox_config/
│   │   ├── sanitizer/
│   │   └── db/
│   └── tests/                (mirror di app/, AAA pattern)
└── frontend/                 (React + Vite, build servita da FastAPI)
    ├── src/
    │   ├── panels/           (un componente per pannello, vedi tabella sopra)
    │   ├── canvas/
    │   ├── store/             (zustand)
    │   ├── api/                (client REST + WS, TanStack Query)
    │   └── eventBus/
    └── vite.config.ts
```
