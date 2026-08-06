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
| `db` | Modelli e accesso SQLite | SQLite |
| `api` | Router FastAPI che espone i moduli sopra + serve la build frontend | — |

**Nota sul parsing dei transcript:** interfaccia isolata e sostituibile (vedi DESIGN.md §3) — resta parsing diretto per l'MVP, non OTel, per non introdurre un collector sempre attivo.

## Componenti frontend

| Pannello | Contenuto | Editing? |
|---|---|---|
| Configuration Manager | Config globale (una recipe attiva alla volta) | Sì (form) |
| Local Package Manager | Pacchetti di progetto (N attivi contemporaneamente) | Sì (form + attivazione) |
| MCP Hub | Elenco, test, attivazione/disattivazione server MCP | Sì (form) |
| Library & Organization | Catalogo skill/agenti/comandi/output style; albero cartelle + filtro tag + preferiti | Solo metadati/organizzazione |
| Token & Cost Dashboard | Grafici costo/token per sessione/progetto/pacchetto/periodo | No (read-only) |
| Live Activity Monitor | Sessioni attive (busy/idle) + drill-down skill/agente/tool | No (read-only) |
| Multi-Agent Monitor *(fase successiva)* | Agent view/team/dynamic workflow | No (read-only) |
| Visual Workflow Canvas | Composizione nodi → pacchetto | Sì (canvas) |
| Workflow Comparator | Diff statico + confronto storico (combinazione / isolato) | No (read-only) |
| Auto Memory Viewer | `MEMORY.md` + storia crescita | Sola lettura/audit |
| Rules Inspector | Regole `.claude/rules/` e pattern | Sola lettura |
| Checkpoint Viewer | Timeline checkpoint + diff | Sola lettura + azione rewind (delega alla CLI) |
| Sandboxing Editor | Allowlist filesystem/rete + simulatore | Sì (form) |
| Output Styles Manager | Catalogo/editor output style | Sì (form) |
| Import/Export | Wizard export sanitizzato / import con risoluzione dipendenze | Sì (mapping) |

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

## Contratto API (bozza)

| Endpoint | Metodo | Scopo |
|---|---|---|
| `/config/global`, `/config/project` | GET/PUT | Configuration Manager |
| `/mcp/servers` | GET/POST/DELETE | MCP Hub |
| `/library` | GET | Library & Organization (skill/agenti/comandi/output style + cartelle/tag/bookmark) |
| `/projects` | GET/POST | Project discovery (auto-scan + aggiunta manuale) |
| `/packages` | GET/POST/PUT/DELETE | Canvas / package registry |
| `/packages/{id}/activate`, `/deactivate` | POST | Activation engine (con diff preview su richiesta) |
| `/telemetry/summary` | GET | Token & Cost Dashboard |
| `/activity/live` | WS | Live Activity Monitor |
| `/packages/compare` | GET `?a=&b=&mode=combination|isolated` | Workflow Comparator |
| `/packages/{id}/export` | GET | Import/Export (con sanitizzazione) |
| `/packages/import` | POST | Import/Export |
| `/memory/{project}` | GET | Auto Memory Viewer |
| `/rules/{project}` | GET | Rules Inspector |
| `/checkpoints/{session_id}` | GET | Checkpoint Viewer |
| `/sandbox/config` | GET/PUT | Sandboxing Editor |
| `/output-styles` | GET/POST | Output Styles Manager |
| `/system/shutdown` | POST | Spegnimento del backend da UI |

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
