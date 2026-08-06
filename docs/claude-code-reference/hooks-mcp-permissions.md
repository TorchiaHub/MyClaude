# Claude Code — Reference: Hooks, MCP, Permessi/Settings

> Documento di reference per la progettazione di un **Claude Code Control Plane** (web app locale che gestisce visivamente hooks, MCP e permessi).

## Fonti

**Documentazione ufficiale (fetch diretto, agosto 2026):**
- https://code.claude.com/docs/en/hooks — Hooks reference completa
- https://code.claude.com/docs/en/mcp — MCP reference completa
- https://code.claude.com/docs/en/settings — settings.json reference completa
- https://code.claude.com/docs/en/permissions — Permessi reference completa
- https://code.claude.com/docs/en/tools-reference — elenco tool nativi (inclusi quelli MCP-correlati)
- https://code.claude.com/docs/en/authentication — precedenza credenziali (contesto per `apiKeyHelper`)

Nota: `docs.claude.com/en/docs/claude-code/*` fa **301 redirect** verso `code.claude.com/docs/en/*` — è il nuovo host canonico della documentazione Claude Code (separato da `platform.claude.com/docs`, che copre l'API Claude/Agent SDK).

**Ground-truth locale verificato su questa macchina:**
- `~/.claude/settings.json` — sezioni `hooks` (29 eventi), `permissions`, più campi top-level reali (`statusLine`, `spinnerVerbs`, `spinnerTipsOverride`, `effortLevel`, `tui`, `theme`, `attribution`, `disableAllHooks`, `enabledPlugins`, `extraKnownMarketplaces`, `skipDangerousModePermissionPrompt`, `preferredNotifChannel`)
- `~/.claude.json` → chiave `mcpServers` (5 server stdio configurati: `ollama`, `obsidian-personal`, `obsidian-zerolang`, `juno-papers`, `skills-vault`)
- Esempi reali di `hooks/hooks.json` da plugin installati: `hookify`, `security-guidance` (quest'ultimo mostra `if`, `asyncRewake`, `rewakeMessage`, `rewakeSummary` in uso reale)
- Nessun `.mcp.json` di progetto trovato sulla macchina (ricerca in `/home/matt/Documents` e sotto `$HOME`, profondità limitata)
- Nessun `.claude/settings.local.json` di progetto trovato nella working directory

**Verifica bug noto (`settings.local.json` non fa merge dei permessi):**
Confermato come bug reale e attivamente tracciato, non comportamento di design — la doc ufficiale dichiara che le regole di permesso "merge across scopes", ma in pratica la scrittura di `settings.local.json` (via dialog "don't ask again" o scrittura programmatica) spesso sovrascrive l'array invece di fonderlo:
- [Issue #19487](https://github.com/anthropics/claude-code/issues/19487) — project `settings.local.json` sovrascrive global invece di deep-merge (gen 2026)
- [Issue #6900](https://github.com/anthropics/claude-code/issues/6900) — scrittura programmatica di `permissions.allow` sovrascrive path aggiunti manualmente
- [Issue #9814](https://github.com/anthropics/claude-code/issues/9814) / [#9875](https://github.com/anthropics/claude-code/issues/9875) — "don't ask again" dalla UI sovrascrive l'intera lista permessi invece di fare append
- [Issue #55507](https://github.com/anthropics/claude-code/issues/55507) — `permissions.defaultMode` a livello user viene ignorato silenziosamente se un file a precedenza più alta contiene un blocco `permissions`

---

## 1. Hooks

### 1.1 Elenco eventi (confermato + ampliato)

I 29 eventi noti dalla ricerca precedente sono confermati letteralmente in `~/.claude/settings.json` locale. La doc ufficiale ne aggiunge uno non presente nell'elenco iniziale: **`DirectoryAdded`**.

| Categoria | Eventi |
|---|---|
| Sessione | `SessionStart`, `Setup`, `SessionEnd` |
| Turno | `UserPromptSubmit`, `UserPromptExpansion`, `Stop`, `StopFailure` |
| Tool call | `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `PermissionRequest`, `PermissionDenied` |
| Altro | `Notification`, `MessageDisplay`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`, `PreCompact`, `PostCompact`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `InstructionsLoaded`, `Elicitation`, `ElicitationResult` |

Totale: **30 eventi** (29 noti + `DirectoryAdded`).

### 1.2 Input JSON su stdin

**Campi comuni a tutti gli eventi:**

```json
{
  "session_id": "abc123",
  "prompt_id": "550e8400-e29b-41d4-a716-446655440000",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "agent_id": "subagent-id",
  "agent_type": "subagent-name",
  "effort": { "level": "medium" }
}
```

| Campo | Note |
|---|---|
| `session_id` | ID sessione corrente |
| `prompt_id` | UUID per correlare con eventi OpenTelemetry (v2.1.196+) |
| `transcript_path` | path al JSONL della conversazione (può essere in ritardo sul turno corrente) |
| `cwd` | working directory corrente |
| `permission_mode` | `default` \| `plan` \| `acceptEdits` \| `auto` \| `dontAsk` \| `bypassPermissions` |
| `agent_id` / `agent_type` | presenti solo in contesto subagent |
| `effort.level` | `low` \| `medium` \| `high` \| `xhigh` \| `max` (anche in env var `$CLAUDE_EFFORT`) |

**Campi aggiuntivi per eventi tool** (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`):

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run test suite",
    "timeout": 120000,
    "run_in_background": false
  },
  "tool_use_id": "toolu_01ABC123...",
  "tool_response": "...",
  "tool_error": "..."
}
```

### 1.3 Exit code e comportamento

| Exit code | Significato | Comportamento |
|---|---|---|
| `0` | Successo | stdout parsato come JSON per output strutturato; stderr solo nel debug log |
| `2` | Errore bloccante | stdout ignorato; stderr passato a Claude; blocca l'azione (varia per evento) |
| Altro | Errore non bloccante | notifica di errore mostrata; l'azione procede comunque |

**Eventi che il codice 2 può bloccare:** `PreToolUse` (blocca la tool call), `PermissionRequest` (nega il permesso), `UserPromptSubmit`/`UserPromptExpansion` (blocca l'elaborazione), `Stop`/`SubagentStop` (impedisce la chiusura, continua la conversazione), `PostToolBatch` (ferma il loop agentic prima della prossima chiamata al modello), `TaskCreated`/`TaskCompleted` (rollback/impedisce), `ConfigChange` (blocca la modifica config), `PreCompact` (blocca la compattazione), `Elicitation`/`ElicitationResult` (nega/blocca la risposta), `WorktreeCreate` (qualunque exit non-zero fa fallire la creazione).

**Eventi dove il codice 2 è solo informativo (non blocca):** `PostToolUse`/`PostToolUseFailure` (il tool è già girato, stderr mostrato a Claude), `PermissionDenied` (output ignorato, serve JSON con `retry: true`), `SessionStart`/`Setup`/`SubagentStart` (stderr solo nel transcript), `Notification`, `FileChanged`, `CwdChanged` ecc. (solo log).

### 1.4 Output JSON strutturato (stdout, exit 0)

**Campi universali:**

| Campo | Default | Descrizione |
|---|---|---|
| `continue` | `true` | se `false`, ferma Claude del tutto dopo l'esecuzione dell'hook |
| `stopReason` | — | messaggio mostrato all'utente quando `continue: false` |
| `suppressOutput` | `false` | nasconde lo stdout dell'hook dal transcript (resta nel debug log) |
| `systemMessage` | — | warning mostrato all'utente |
| `terminalSequence` | — | sequenza OSC per notifica desktop, titolo finestra, o bell |

**Output specifico per evento** (esempi):

`PreToolUse`:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask|defer",
    "permissionDecisionReason": "Reason text",
    "updatedInput": { "command": "modified command" }
  }
}
```

`PermissionRequest`:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": { "behavior": "allow|deny", "updatedInput": {} }
  }
}
```

`PostToolUse`:
```json
{
  "decision": "block",
  "reason": "Error found in output",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "updatedToolOutput": "Modified output",
    "additionalContext": "Claude-visible feedback"
  }
}
```

`PermissionDenied`:
```json
{ "hookSpecificOutput": { "hookEventName": "PermissionDenied", "retry": true } }
```

`Stop` / `SubagentStop`:
```json
{
  "decision": "block",
  "reason": "Continue for more context",
  "hookSpecificOutput": { "hookEventName": "Stop", "additionalContext": "Non-error feedback" }
}
```

`Elicitation` / `ElicitationResult`:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "Elicitation",
    "action": "accept|decline|cancel",
    "content": { "field_name": "value" }
  }
}
```

`SessionStart`:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Context for Claude",
    "initialUserMessage": "Optional first message",
    "watchPaths": ["*.md", ".env"],
    "sessionTitle": "Custom title",
    "reloadSkills": true
  }
}
```

`WorktreeCreate`: l'hook di tipo command deve stampare il path del worktree su stdout, oppure restituire:
```json
{ "hookSpecificOutput": { "hookEventName": "WorktreeCreate", "worktreePath": "/path/to/worktree" } }
```

### 1.5 Sintassi dei `matcher`

| Tipo pattern | Esempio | Comportamento |
|---|---|---|
| `"*"`, `""`, omesso | — | matcha tutte le occorrenze |
| Match esatto (lettere, cifre, `_`, `-`, spazi, `,`, `\|`) | `Bash`, `Edit\|Write`, `code-reviewer` | stringa esatta o lista separata da pipe/virgola |
| Regex (contiene altri caratteri) | `^Notebook`, `mcp__.*__write.*` | regex JavaScript, non ancorata |

**Cosa filtra il matcher, per evento:**

| Evento | Matcher filtra su | Esempi |
|---|---|---|
| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied` | nome tool | `Bash`, `Edit\|Write`, `mcp__memory__.*` |
| `SessionStart` | motivo avvio | `startup`, `resume`, `clear`, `compact`, `fork` |
| `Setup` | flag CLI | `init`, `maintenance` |
| `SessionEnd` | motivo fine | `clear`, `resume`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other` |
| `Notification` | tipo notifica | `permission_prompt`, `idle_prompt`, `auth_success`, ... |
| `SubagentStart`, `SubagentStop` | tipo agente | `general-purpose`, `Explore`, `Plan`, o nomi custom |
| `ConfigChange` | sorgente config | `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills` |
| `DirectoryAdded` | metodo aggiunta | `slash_command`, `register_repo_root` |
| `FileChanged` | glob nome file | `.envrc\|.env` (solo set match-esatto: lettere, cifre, `_`, `\|`) |
| `StopFailure` | tipo errore | `rate_limit`, `overloaded`, `authentication_failed`, ... |
| `InstructionsLoaded` | motivo caricamento | `session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact` |
| `UserPromptExpansion`, `Elicitation`, `ElicitationResult` | nome skill/server MCP | — |
| `PreCompact`, `PostCompact` | sorgente trigger | `manual`, `auto` |
| `UserPromptSubmit`, `PostToolBatch`, `Stop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`, `MessageDisplay`, `CwdChanged` | nessun matcher supportato | scattano sempre |

**Match su tool MCP:** `mcp__<server>__<tool>`, es. `mcp__memory__.*`. Per server MCP forniti da plugin: `mcp__plugin_<plugin-name>_<server-name>__<tool-name>` (ogni carattere fuori da `A-Z a-z 0-9 _ -` diventa `_`). Un matcher scritto sul nome server "nudo" (`mcp__database-tools__.*`) **non** scatta mai per un server bundlato in un plugin.

### 1.6 Struttura configurazione hooks

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolName",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/script.sh",
            "args": [],
            "if": "Bash(rm *)",
            "timeout": 600,
            "statusMessage": "Checking...",
            "async": false,
            "asyncRewake": false,
            "shell": "bash"
          }
        ]
      }
    ]
  },
  "disableAllHooks": false
}
```

**Dove vivono i file di config hooks:**

| Location | Scope | Condivisibile |
|---|---|---|
| `~/.claude/settings.json` | tutti i progetti | No (locale) |
| `.claude/settings.json` | singolo progetto | Sì (commit in repo) |
| `.claude/settings.local.json` | singolo progetto | No (gitignored) |
| Managed policy settings | org-wide | Sì (admin) |
| Plugin `hooks/hooks.json` | quando il plugin è abilitato | Sì (bundlato) |
| Frontmatter skill/agent | mentre attivo | Sì (nel file) |

### 1.7 Tipi di hook handler (5, non solo `command`)

**1. `command`** — comando shell/eseguibile.
```json
{
  "type": "command",
  "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/check.sh",
  "args": [],
  "timeout": 600,
  "statusMessage": "Running checks...",
  "async": false,
  "asyncRewake": false,
  "shell": "bash"
}
```
- `args` presente → **exec form** (niente shell, ogni arg passato letteralmente, niente injection)
- `args` omesso → **shell form** (shell tokenizza, espande variabili, interpreta pipe/redirect)

**2. `http`** — endpoint HTTP.
```json
{
  "type": "http",
  "url": "http://localhost:8080/hooks/pre-tool-use",
  "timeout": 30,
  "headers": { "Authorization": "Bearer $MY_TOKEN" },
  "allowedEnvVars": ["MY_TOKEN"]
}
```
POST con body JSON, risposta 2xx processata come output JSON standard, non-2xx = errore non bloccante.

**3. `mcp_tool`** — chiama un tool MCP configurato come hook.
```json
{
  "type": "mcp_tool",
  "server": "my_server",
  "tool": "security_scan",
  "input": { "file_path": "${tool_input.file_path}" },
  "timeout": 600
}
```
`server` accetta anche `plugin:<name>:<key>` per server bundlati in plugin.

**4. `prompt`** — invoca un modello con un prompt.
```json
{ "type": "prompt", "prompt": "Is this command safe? Explain: $ARGUMENTS", "model": "claude-3-5-sonnet", "timeout": 30 }
```

**5. `agent`** — spawna un subagent con accesso a Read/Grep/Glob.
```json
{ "type": "agent", "prompt": "Verify the file is safe: $ARGUMENTS", "timeout": 60 }
```

**Campi comuni a tutti i tipi:** `if` (filtro sintassi regola permessi, es. `"Bash(git *)"` — valutato solo su eventi tool), `timeout` (default varia per evento: 600s standard, 30s per `UserPromptSubmit`, 10s per `MessageDisplay`), `statusMessage` (testo spinner), `once` (esegue una volta per sessione poi si rimuove — solo skill/agent).

### 1.8 `async` / `asyncRewake` / `once`

- **`async: true`** — esegue in background senza bloccare il turno.
- **`asyncRewake: true`** — esegue in background, "risveglia" Claude se l'hook esce con codice 2 (implica `async`). Usato in produzione dal plugin `security-guidance` per review di sicurezza asincrone su `git commit`/`git push`, con campi aggiuntivi `rewakeMessage` e `rewakeSummary` (confermato da `hooks.json` reale sulla macchina).
- **`once: true`** — esegue una volta per sessione poi si auto-rimuove (solo per hook dichiarati in skill/agent).

### 1.9 Timeout

- Default: 600 secondi (10 minuti) per hook `command` standard.
- Override per evento: 30s per `UserPromptSubmit`, 10s per `MessageDisplay`, 5000ms tipico nella config locale (in ms nel formato legacy visto in `~/.claude/settings.json`, in secondi nel formato documentato — **attenzione all'unità**: la doc ufficiale usa secondi interi (`"timeout": 600`), ma la config osservata sulla macchina usa millisecondi (`"timeout": 5000`) — verificare la versione installata, il campo potrebbe accettare entrambe le unità in modo euristico o essere cambiato tra versioni).
- Alla scadenza: l'hook viene cancellato, il comportamento dipende dall'evento (vedi tabella exit code — un timeout è trattato come errore non bloccante salvo diversamente specificato).

### 1.10 Path placeholder e variabili d'ambiente

| Placeholder | Descrizione |
|---|---|
| `${CLAUDE_PROJECT_DIR}` | root del progetto |
| `${CLAUDE_PLUGIN_ROOT}` | directory di installazione del plugin (cambia ad ogni update) |
| `${CLAUDE_PLUGIN_DATA}` | directory dati persistenti del plugin |

Esportate anche come env var nei processi spawnati. Altre env var disponibili negli hook:
`$CLAUDE_PROJECT_DIR`, `$CLAUDE_PLUGIN_ROOT`, `$CLAUDE_PLUGIN_DATA`, `$CLAUDE_EFFORT`, `$CLAUDE_CODE_REMOTE` (="true" in ambienti web), `$CLAUDE_CODE_BRIDGE_SESSION_ID` (Remote Control, v2.1.199+), più l'environment del parent process (esclusi `OTEL_*`). Gli hook di plugin ricevono anche `$CLAUDE_PLUGIN_OPTION_<KEY>` per valori di configurazione utente.

### 1.11 Sicurezza

- Preferire `args` (exec form) a stringhe shell per prevenire injection.
- Allowlist per hook HTTP: `allowedHttpHookUrls` (pattern URL, `*` come wildcard) e `httpHookAllowedEnvVars`.
- Policy managed: `allowManagedHooksOnly: true` blocca hook utente/progetto (i plugin force-enabled in managed settings sono esenti).
- Debug: `"debugLogging": true` in settings mostra input JSON completo, stdout/stderr, dettagli parsing JSON, timeout e fallimenti.
- `/hooks` in-app mostra tutti gli hook configurati, con evento, matcher, tipo e file sorgente (sola lettura).

### 1.12 Plugin hooks — conferma pattern additivo

Confermato con esempi reali locali: i plugin dichiarano `hooks/hooks.json` alla radice del plugin (path relativo, `${CLAUDE_PLUGIN_ROOT}` per riferimenti assoluti agli script), e Claude Code li fonde automaticamente senza toccare `settings.json`. Esempio (`hookify`, `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/hookify/hooks/hooks.json`): hook su `PreToolUse`, `PostToolUse`, `Stop`, `UserPromptSubmit`, ognuno che invoca uno script Python nella cartella del plugin. Il `plugin.json` del plugin **non** deve dichiarare esplicitamente la cartella hooks — è una convenzione di path fissa (`hooks/hooks.json` dentro la root del plugin).

---

## 2. MCP (Model Context Protocol)

### 2.1 Transport supportati

| Transport | Stato | Note |
|---|---|---|
| `stdio` | Consigliato per server locali | Processo locale, accesso diretto al filesystem/sistema |
| `http` (alias `streamable-http`) | **Consigliato per server remoti** | Supporta OAuth 2.0, riconnessione automatica |
| `sse` (Server-Sent Events) | **Deprecato** | usare `http` dove disponibile |
| `ws` (WebSocket) | Per server che devono spingere eventi non richiesti | Nessun supporto OAuth (solo header statici o `headersHelper`); non compare in `claude mcp list`, solo in `/mcp` o `claude mcp get` |

Un entry JSON con `url` ma senza `type` è un errore di configurazione: Claude Code lo interpreta come server `stdio` e lo salta, con warning `MCP server "<name>" has a "url" but no "type"; add "type": "http" (or "sse" / "ws") to this entry`.

### 2.2 Schema di configurazione

**Formato `.mcp.json` (progetto) / entry in `~/.claude.json` (globale/locale):**

```json
{
  "mcpServers": {
    "stripe": { "type": "http", "url": "https://mcp.stripe.com" },
    "db": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub", "--dsn", "postgresql://..."],
      "env": {}
    },
    "events-server": {
      "type": "ws",
      "url": "wss://mcp.example.com/socket",
      "headers": { "Authorization": "Bearer YOUR_TOKEN" }
    }
  }
}
```

Campi per tipo `http`/`sse`/`ws`: `url`, `headers`, `headersHelper`, `timeout`, `alwaysLoad`, `oauth` (vedi §2.4).
Campi per tipo `stdio`: `command`, `args`, `env`, `timeout`.

**Espansione variabili d'ambiente** in `.mcp.json`: `${VAR}` e `${VAR:-default}`, applicabile a `command`, `args`, `env`, `url`, `headers`. Se la variabile non è settata e non c'è default, il config si carica comunque con un warning e il testo `${VAR}` non espanso.

### 2.3 Scope di installazione

| Scope | Loading | Condiviso col team | Storage |
|---|---|---|---|
| **Local** (default) | solo progetto corrente | No | `~/.claude.json` (sotto path del progetto) |
| **Project** | solo progetto corrente | Sì (via VCS) | `.mcp.json` in root progetto |
| **User** | tutti i progetti | No | `~/.claude.json` (globale) |

Comandi: `claude mcp add --transport <stdio|http|sse> [--scope local|project|user] <name> <url|-- comando>`, `claude mcp add-json <name> '<json>'`, `claude mcp list`, `claude mcp get <name>`, `claude mcp remove <name>`, `claude mcp reset-project-choices`.

**Precedenza quando lo stesso server è definito in più posti** (usa la definizione dalla sorgente a precedenza più alta, senza merge dei campi):
1. Local scope
2. Project scope
3. User scope
4. Server forniti da plugin
5. Connector claude.ai

I tre scope fanno match per nome; plugin e connector fanno match per endpoint (stessa URL/comando = duplicato).

**Ground-truth locale**: i 5 server MCP configurati (`ollama`, `obsidian-personal`, `obsidian-zerolang`, `juno-papers`, `skills-vault`) sono tutti in `~/.claude.json` chiave `mcpServers` — cioè scope globale/user, non legati a un progetto specifico. Tutti stdio tranne implicitamente da verificare (mancava `"type"` esplicito su `obsidian-personal`/`obsidian-zerolang`/`juno-papers` — se manca `type` e non c'è `url`, viene trattato come stdio di default).

### 2.4 Autenticazione OAuth per MCP

Sì, esiste, solo per transport `http`/`sse` (non stdio, non ws se non via header statico).

- **Discovery automatica**: prima RFC 9728 (`/.well-known/oauth-protected-resource`), poi fallback RFC 8414 (`/.well-known/oauth-authorization-server`). Override con `oauth.authServerMetadataUrl`.
- **Dynamic Client Registration** di default; supporto anche per **Client ID Metadata Document (CIMD)**.
- **Credenziali pre-configurate**: `claude mcp add --client-id ... --client-secret --callback-port 8080` oppure via JSON: `"oauth": {"clientId": "...", "callbackPort": 8080}`.
- **Scope ristretti**: `oauth.scopes` (stringa singola separata da spazi) forza un subset di scope approvato, ha precedenza su discovery automatica.
- **Flusso**: `/mcp` in-app avvia il browser login; `claude mcp login <name>` / `claude mcp logout <name>` da CLI (v2.1.186+), con `--no-browser` per SSH/headless.
- **Auth non-OAuth**: `headersHelper` — comando che genera header dinamicamente ad ogni connessione (utile per Kerberos, token short-lived, SSO interno). Nessun caching integrato.
- Claude Code marca un server come "needs authentication" su risposta `401`/`403`; su refresh fallito ritenta una volta poi flagga in `/mcp`.

### 2.5 Come un server MCP espone tool/risorse/prompt

- **Tool**: esposti via `tools/list`; naming lato Claude Code è `mcp__<server>__<tool>`. Per server bundlati in plugin: `mcp__plugin_<plugin-name>_<server-name>__<tool-name>`.
- **Risorse**: esposte via `resources/list`, referenziabili in prompt con `@server:protocol://resource/path` (es. `@github:issue://123`, `@docs:file://api/authentication`). Autocomplete su digitazione di `@`.
- **Prompt**: esposti via `prompts/list`, diventano slash command `/mcp__servername__promptname`, con argomenti passati come stringa separata da spazi.
- **Notifiche dinamiche**: supporto per `list_changed` — un server MCP può aggiornare tool/prompt/risorse a runtime senza richiedere riconnessione.
- **Elicitation**: un server può richiedere input strutturato a runtime (form mode o URL mode); Claude Code mostra un dialog automaticamente, oppure un hook `Elicitation`/`ElicitationResult` può auto-rispondere.
- **Annotazioni `_meta` per autori di server MCP**:
  - `anthropic/maxResultSizeChars` — alza il limite di output per un tool specifico (fino a 500.000 caratteri), indipendente da `MAX_MCP_OUTPUT_TOKENS`.
  - `anthropic/requiresUserInteraction: true` — forza il prompt di conferma su ogni chiamata, anche in `acceptEdits`/`auto`/`bypassPermissions`, mai "don't ask again".
  - `anthropic/alwaysLoad: true` — carica il tool sempre in context invece di deferirlo al tool search.

### 2.6 Tool search (rilevante per gestione contesto)

Di default **abilitato**: i tool MCP sono deferiti (solo nomi + istruzioni server caricati all'avvio), scoperti on-demand via tool `ToolSearch` quando servono. Configurabile con env var `ENABLE_TOOL_SEARCH` (`true`/`auto`/`auto:N`/`false`). Un server può forzare il caricamento upfront con `alwaysLoad: true` nel proprio config.

### 2.7 Tool nativi `ListMcpResourcesTool` / `ReadMcpResourceTool`

Confermato dalla reference ufficiale dei tool (`/docs/en/tools-reference`):

| Tool | Descrizione | Permesso richiesto (default mode) |
|---|---|---|
| `ListMcpResourcesTool` | Elenca le risorse esposte dai server MCP connessi | No |
| `ReadMcpResourceTool` | Legge una risorsa MCP specifica per URI | No |

**Correzione rispetto al brief iniziale**: `ReadMcpResourceDirTool` **non risulta nella documentazione ufficiale attuale** — non è menzionato nella tools-reference né altrove nella doc MCP. Solo `ListMcpResourcesTool` e `ReadMcpResourceTool` sono i tool nativi documentati per l'interazione con risorse MCP. Possibile che sia un nome obsoleto, sperimentale, o mai esistito nella forma cercata — da verificare con `/status` o `--verbose` su un'installazione reale se serve certezza assoluta.

Questi tool nativi sono il meccanismo generico con cui Claude accede a risorse esposte da *qualunque* server MCP connesso, senza bisogno che il server stesso registri un tool ad-hoc per "list"/"read" — coprono l'intera capability `resources` del protocollo MCP.

### 2.8 Altri dettagli operativi rilevanti per un control plane

- **Nomi server riservati** (non usabili): `workspace`, `claude-in-chrome`, `computer-use`, `Claude Preview`, `Claude Browser`.
- **Toggle on/off senza rimuovere**: dal pannello `/mcp`, salvato per progetto in `~/.claude.json` in due liste disgiunte: `disabledMcpServers` (opt-out, per server default-on) e `enabledMcpServers` (opt-in, per server default-off come `computer-use`).
- **Timeout**: `timeout` per-server in ms nel config (hard wall-clock limit per tool call); env var globale `MCP_TOOL_TIMEOUT` (default ~28h se non settato); idle timeout separato (`CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT`, default 5 min per http/sse/ws, 30 min per stdio).
- **Output limit**: warning oltre 10.000 token, cap default 25.000 token (`MAX_MCP_OUTPUT_TOKENS` per alzarlo).
- **Backgrounding automatico**: una chiamata MCP nella conversazione principale che supera 2 minuti passa automaticamente a task in background (non blocca la sessione).
- **Riconnessione automatica**: per http/sse, fino a 5 tentativi con backoff esponenziale (1s iniziale, raddoppia). stdio non si riconnette automaticamente.
- **`claude mcp serve`**: Claude Code stesso può fare da server MCP stdio per altre applicazioni (es. Claude Desktop), esponendo i tool nativi come Read/Edit/LS.

### 2.9 Managed MCP configuration (enterprise)

Campi solo-managed rilevanti: `allowedMcpServers` (allowlist), `deniedMcpServers` (denylist, ha precedenza), `allowManagedMcpServersOnly` (blocca configurazioni utente/progetto), `allowAllClaudeAiMcps` (permette connector claude.ai insieme a `managed-mcp.json`).

---

## 3. Permessi / Settings

### 3.1 Modalità di permesso (permission modes)

Confermato: sono **6**, non solo i 4 citati nel brief iniziale.

| Mode | Alias/Label | Descrizione |
|---|---|---|
| `default` | `manual` (v2.1.200+) | prompt al primo uso di ogni tool |
| `acceptEdits` | — | auto-accetta edit di file e comandi filesystem comuni (`mkdir`, `touch`, `mv`, `cp`) dentro working directory/`additionalDirectories` |
| `plan` | Plan | solo lettura/esplorazione, nessun edit; con auto mode, comandi classificati come sicuri girano comunque |
| `auto` | — | auto-approva le tool call con controlli di sicurezza in background che verificano l'allineamento con la richiesta |
| `dontAsk` | — | auto-nega i tool non pre-approvati via `/permissions` o `permissions.allow`; nega sempre `AskUserQuestion`, tool connector marcati `ask` dall'org, e tool MCP `requiresUserInteraction` |
| `bypassPermissions` | — | salta i prompt tranne regole `ask` esplicite, connector `ask`-marked, e tool MCP `requiresUserInteraction`; `rm -rf /` o `rm -rf ~` restano comunque bloccati come circuit breaker |

Impostabile via `defaultMode` nei file settings. `disableBypassPermissionsMode` / `permissions.disableAutoMode` possono impedire l'uso di `bypassPermissions`/`auto` (utile in managed settings, dove non è overridabile).

`bypassPermissions` salta i prompt **anche** per scritture in `.git`, `.config/git`, `.claude`, `.vscode`, `.idea`, `.husky`, `.cargo`, `.devcontainer`, `.yarn`, `.mvn` — usare solo in ambienti isolati (container/VM).

### 3.2 Sintassi delle regole di permesso

Formato generale: `Tool` (matcha tutto) o `Tool(specifier)` (matcha uso specifico).

**Regole per Bash/PowerShell** (wildcard `*` in qualunque posizione, spazio prima di `*` impone confine di parola: `Bash(ls *)` matcha `ls -la` ma non `lsof`; `Bash(ls*)` matcha entrambi; suffisso `:*` equivalente a ` *` finale):
```
Bash(npm run build)        → match esatto
Bash(npm run test *)       → prefisso
Bash(npm *)                → prefisso ampio
Bash(* install)            → suffisso
Bash(git * main)           → wildcard centrale
```
Claude Code riconosce operatori shell (`&&`, `||`, `;`, `|`, `|&`, `&`, newline) — una regola deve matchare *ogni* subcomando indipendentemente; non basta matchare il primo. Wrapper noti (`timeout`, `time`, `nice`, `nohup`, `stdbuf`, `command`, `builtin`, zsh `noglob`) vengono "spogliati" prima del match, quindi `Bash(npm test *)` matcha anche `timeout 30 npm test`. Runner come `npx`, `docker exec`, `direnv exec` **non** sono nella lista wrapper — vanno scritte regole esplicite complete (`Bash(devbox run npm test)`).

**Read/Edit** — sintassi gitignore-style con 4 tipi di ancoraggio:

| Pattern | Significato | Esempio |
|---|---|---|
| `//path` | assoluto da filesystem root | `Read(//Users/alice/secrets/**)` |
| `~/path` | da home directory | `Read(~/Documents/*.pdf)` |
| `/path` | relativo alla sorgente del file settings | `Edit(/src/**/*.ts)` |
| `path` o `./path` | relativo alla cwd | `Read(*.env)` |

Nota critica: un pattern come `/Users/alice/file` **non** è un path assoluto — un singolo slash iniziale ancora alla sorgente del settings file, non al filesystem root. Serve `//` per l'assoluto vero.

Le regole `Edit` coprono *tutti* i tool che editano file (Write, NotebookEdit, MultiEdit inclusi) — scrivere una regola su `Write(...)` o `NotebookEdit(...)` viene accettato ma **mai consultato** (warning a startup). Usare sempre `Edit(path)`.

**WebFetch:**
```
WebFetch(domain:example.com)     → match esatto
WebFetch(domain:*.example.com)   → qualunque sottodominio a qualunque profondità
WebFetch(domain:*)               → tutti i domini
```

**MCP:**
```
mcp__puppeteer                       → qualunque tool del server puppeteer
mcp__puppeteer__*                    → equivalente, wildcard esplicito
mcp__puppeteer__puppeteer_navigate   → tool specifico
```

**Agent (subagent):** `Agent(Explore)`, `Agent(Plan)`, `Agent(my-custom-agent)` — tipicamente in `deny` per disabilitare subagent specifici.

**Cd** (controlla `/cd`, non è model-invocable): `Cd(~/code/*)` matcha solo `~/code/app` (un livello), `Cd(~/code/**)` ricorsivo.

**Match su parametro di input** (solo deny/ask, non allow): `Tool(param:value)` su qualunque campo scalare top-level dell'input — es. `Agent(model:opus)`, `Bash(run_in_background:true)`. Non applicabile ai campi "contenuto primario" (`command` per Bash, `file_path` per Read/Edit/Write, `url` per WebFetch) — Claude Code li ignora con warning perché aggirabili banalmente.

### 3.3 Ordine di valutazione: deny → ask → allow

**Confermato esplicitamente**: le regole sono valutate in ordine deny, poi ask, poi allow. Il primo match in quest'ordine determina l'esito — **la specificità della regola non cambia l'ordine**. Una deny ampia (`Bash(aws *)`) blocca anche una call che matcha una allow più specifica (`Bash(aws s3 ls)`); una deny non può avere "eccezioni" allowlist. Stessa logica tra ask e allow: una ask che matcha prompta anche se una allow più specifica matcha la stessa call.

Deny su nome tool "nudo" (`Bash`) rimuove il tool dal contesto di Claude — non lo vede proprio (eccetto `EndConversation`, mai rimovibile mentre resta almeno un altro tool). Deny scoped (`Bash(rm *)`) lascia il tool disponibile ma blocca le call che matchano.

Gli **hook `PreToolUse` non bypassano le regole di permesso**: anche se l'hook ritorna `"allow"`, una deny/ask rule matchante si applica comunque. Un hook che blocca (`exit 2`) invece ha precedenza sulle allow — il blocco avviene *prima* della valutazione delle regole di permesso.

### 3.4 Gerarchia dei file settings e merge

**5 livelli di precedenza** (dal più alto al più basso):

1. **Managed settings** — nessun altro livello (nemmeno CLI args) può sovrascrivere una regola di permesso managed. Delivery: server-managed via claude.ai admin console, MDM/OS policy (plist macOS, registro Windows), file `managed-settings.json` + drop-in `managed-settings.d/*.json`.
2. **Command line arguments** — override temporanei di sessione.
3. **Local project settings** (`.claude/settings.local.json`) — personale, non condiviso (gitignored di default).
4. **Shared project settings** (`.claude/settings.json`) — condiviso col team via VCS.
5. **User settings** (`~/.claude/settings.json`) — personale, cross-progetto.

**Regola di merge per i permessi**: se un tool è negato a un livello qualsiasi, nessun livello più basso può riabilitarlo. Se user settings permette e project settings nega, vince la negazione (e viceversa) — **le regole deny da qualsiasi scope sono valutate prima delle allow**. Le regole di permesso dovrebbero fondersi (concatenare gli array `allow`/`ask`/`deny`) attraverso gli scope — **ma vedi il bug noto documentato in cima al file**: la scrittura pratica di `settings.local.json` (via UI o programmatica) spesso sovrascrive l'intero array invece di fare append/merge.

**Altri campi non-permesso** seguono override semplice per chiave (non merge): es. `spinnerTipsEnabled: true` in user + `false` in project → vince project (valore più specifico vince, non somma).

### 3.5 Altri campi rilevanti di `settings.json`

Oltre a `hooks` e `permissions`, confermati e ampliati rispetto al brief:

**Modello:**
| Campo | Tipo | Descrizione |
|---|---|---|
| `model` | string | modello primario (letto all'avvio sessione) |
| `fallbackModel` | array | catena di fallback se il primario è overloaded (max 3) |
| `advisorModel` | string | modello advisor server-side |
| `availableModels` | array | restringe i modelli selezionabili |
| `effortLevel` | string | `low`\|`medium`\|`high`\|`xhigh` — **confermato in uso locale**: `"high"` |
| `alwaysThinkingEnabled` | boolean | extended thinking di default |

**UI/UX** (**confermati in uso locale**):
| Campo | Valore locale osservato | Descrizione |
|---|---|---|
| `statusLine` | `{"type":"command","command":"echo '🐧 claude-code: ready'","padding":0}` | comando custom per la status line |
| `spinnerVerbs` | `{"mode":"replace","verbs":[...]}` | messaggi custom durante lo spinner (in italiano nella config locale) |
| `spinnerTipsOverride` | `{"excludeDefault":false,"tips":[...]}` | tip custom mostrati durante lo spinner |
| `tui` | `"fullscreen"` | modalità terminal UI |
| `theme` | `"dark"` | tema |
| `editorMode` | — (non settato) | `normal`\|`vim`, default `normal` |

**Automazione:**
`agent` (esegue il thread principale come subagent nominato), `autoCompactEnabled` (default `true`), `autoCompactWindow` (soglia token, 100k–1M), `autoMode` (regole classificatore auto mode: `allow`, `soft_deny`, `hard_deny`, `environment`), `autoMemoryEnabled`/`autoMemoryDirectory`, `awaySummaryEnabled`, `askUserQuestionTimeout`.

**Hook-correlati:**
`disableAllHooks` (**confermato locale**: `false` — disabilita anche la status line custom se `true`), `allowedHttpHookUrls`, `allowManagedHooksOnly`.

**Git/attribution** (**confermato locale**):
```json
"attribution": {
  "commit": "Co-Authored-By: Claude <noreply@anthropic.com>",
  "pr": "Generated with [Claude Code](https://claude.ai/code)"
}
```
Più `includeCoAuthoredBy` (boolean, aggiunge/rimuove footer Co-Authored-By).

**MCP-correlati** (settings, non `mcpServers` stesso):
`allowedMcpServers`/`deniedMcpServers` (managed), `allowManagedMcpServersOnly` (managed), `enableAllProjectMcpServers` (auto-approva tutti i server di `.mcp.json`), `enabledMcpjsonServers`/`disabledMcpjsonServers` (approvazione selettiva per nome), `disableClaudeAiConnectors`.

**Env e auth:**
```json
"env": { "CLAUDE_CODE_ENABLE_TELEMETRY": "1", "OTEL_METRICS_EXPORTER": "otlp" }
```
`apiKeyHelper` (script custom per generare credenziali, inviate come header `X-Api-Key` + `Authorization: Bearer`; refresh dopo 5 min o su HTTP 401), `defaultShell` (default `bash`/`powershell`).

**Plugin locali confermati** (`enabledPlugins`, `extraKnownMarketplaces`): la config locale ha 19 plugin abilitati (feature-dev, frontend-design, security-guidance, hookify, claude-mem, playwright, context7, ecc.) da 3 marketplace (`claude-plugins-official`, `l3digitalnet-plugins`, `thedotmack`).

**Altri campi osservati solo localmente (non ancora nella doc pubblica consultata, verificare in futuro):**
`skipDangerousModePermissionPrompt: true`, `preferredNotifChannel: "notifications_disabled"` — probabili flag più recenti o specifici della build installata.

**Manutenzione:** `cleanupPeriodDays` (default 30, minimo 1), `autoUpdatesChannel` (`latest`|`stable`).

### 3.6 Campi solo-managed (enterprise policy)

Non hanno effetto se messi in user/project settings — solo in managed settings:
`allowedMcpServers`, `deniedMcpServers`, `allowManagedMcpServersOnly`, `allowManagedPermissionRulesOnly`, `allowManagedHooksOnly`, `forceLoginMethod`, `forceLoginOrgUUID`, `claudeMd` (CLAUDE.md org-wide), `strictKnownMarketplaces`, `blockedMarketplaces`, `requiredMinimumVersion`/`requiredMaximumVersion`, `disableSideloadFlags`, `disableSkillShellExecution`, `strictPluginOnlyCustomization`, `channelsEnabled`, `wslInheritsWindowsSettings`, `sandbox.filesystem.allowManagedReadPathsOnly`, `sandbox.network.allowManagedDomainsOnly`.

### 3.7 Working directories e trust

- `--add-dir <path>` (startup), `/add-dir` (in sessione), `additionalDirectories` (persistente in settings) estendono l'accesso file oltre la cwd di lancio.
- **Differenza importante**: directory aggiunte con `--add-dir`/`/add-dir` caricano anche skill, subagent, e (parzialmente) settings/CLAUDE.md da quella directory; directory in `permissions.additionalDirectories` **danno solo accesso file**, non caricano configurazione.
- **Workspace trust**: le regole `allow` e `additionalDirectories` di un progetto (`.claude/settings.json`) si applicano solo dopo che l'utente accetta il trust dialog per quel workspace. `deny`/`ask` non sono soggette a trust check (limitano soltanto). `.claude/settings.local.json` di solito è esente dal trust check (è "tuo"), tranne quando il repo potrebbe averlo fornito (committato o `.claude` è un symlink).

### 3.8 Permessi + Sandboxing (livelli complementari)

- **Permessi**: controllano quali tool Claude Code può usare e quali file/domini può accedere — enforcement lato Claude Code.
- **Sandboxing**: enforcement OS-level che restringe accesso filesystem/rete del tool Bash e dei suoi processi figli — non copre gli altri tool.
- Con sandboxing attivo e `autoAllowBashIfSandboxed` (default `true`), i comandi Bash sandboxed girano senza prompt anche con una regola ask `Bash` generica — il boundary del sandbox sostituisce quel prompt whole-tool (eccetto in plan mode, dove questa sostituzione non si applica).

---

## 4. Riepilogo per il Control Plane — implicazioni di design

Alcuni punti che meritano attenzione UI/UX specifica per una web app che gestisce visivamente questi tre sistemi:

1. **Hooks**: 30 eventi × 5 tipi di handler × campi condizionali (`if`, `async`, `asyncRewake`, `once`, `matcher` con semantica diversa per evento) — la UI deve mostrare solo i campi rilevanti per evento+tipo selezionato, e per gli eventi tool deve offrire un builder di matcher basato sui tool realmente disponibili (inclusi MCP `mcp__server__tool`).
2. **MCP**: 3 scope (local/project/user) + plugin + claude.ai connector, con precedenza per nome (scope) vs per endpoint (plugin/connector) — la UI deve disambiguare chiaramente "dove verrà scritta" una nuova entry e mostrare eventuali duplicati/oscuramenti.
3. **Permessi**: l'ordine deny→ask→allow è fisso e non intuitivo (una regola più specifica NON vince su una più generica di priorità superiore) — vale la pena che il control plane simuli/spieghi visivamente "quale regola vincerebbe" per un dato tool+input, dato il bug noto di non-merge tra settings.local.json e user settings.
4. **Gerarchia file**: 5 livelli con anchoring diverso per i path (`/path` si ancora alla *sorgente del file settings*, non alla cwd) — un editor visivo che non distingue bene "in quale file sto scrivendo questa regola" produce path bug silenziosi.
