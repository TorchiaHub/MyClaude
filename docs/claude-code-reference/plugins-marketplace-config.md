# Claude Code — Plugin, Marketplace e Mappa Configurazione (Reference Completa)

> Documento di reference per la progettazione di un "Claude Code Control Plane" visivo.
> Copre: schema completo di `plugin.json`, schema completo di `marketplace.json`, meccanica di installazione/cache, e mappa esaustiva di tutti i file di configurazione con precedenza tra loro.

## Fonti

**Fonti primarie (fetch diretto, agosto 2026):**
- https://code.claude.com/docs/en/plugins — Create plugins
- https://code.claude.com/docs/en/plugin-marketplaces — Create and distribute a plugin marketplace
- https://code.claude.com/docs/en/plugins-reference — Plugins reference (schema completo)
- https://code.claude.com/docs/en/discover-plugins — Discover and install prebuilt plugins
- https://code.claude.com/docs/en/settings — Settings (file di configurazione, precedenza)
- https://code.claude.com/docs/en/mcp — MCP (scope, precedenza, `.mcp.json`)

**Ground-truth locale (macchina utente, verificata via filesystem):**
- `~/.claude/plugins/installed_plugins.json`
- `~/.claude/plugins/known_marketplaces.json`
- `~/.claude/plugins/marketplaces/*/.claude-plugin/marketplace.json` (3 marketplace reali: `claude-plugins-official`, `l3digitalnet-plugins`, `thedotmack`)
- `~/.claude/plugins/cache/*/*/*/.claude-plugin/plugin.json` (plugin reali: `feature-dev`, `context7`, `claude-mem` v13.13.1, `rust-analyzer-lsp`)
- `~/.claude/marketplace.json` (marketplace ECC locale)
- `~/.claude.json` (612+ chiavi top-level, incl. `mcpServers`, `projects`)
- `~/.claude/settings.json` (config utente reale con hooks, `enabledPlugins`, `extraKnownMarketplaces`)
- Progetti locali con `.mcp.json`, `.claude/` a livello progetto

---

## 1. Plugin

### 1.1 Cos'è un plugin

Un plugin è una directory autonoma che raggruppa in un'unica unità installabile: **skill, agenti, comandi, hook, server MCP, server LSP, monitor, temi, output style**. È l'alternativa "condivisibile e versionata" alla configurazione standalone in `.claude/` (personale, non versionata, nomi corti tipo `/hello` invece di `/plugin-name:hello`).

| Approccio | Namespace skill | Adatto a |
|---|---|---|
| Standalone (`.claude/`) | `/hello` | workflow personali, customizzazioni di progetto, esperimenti |
| Plugin | `/plugin-name:hello` | condivisione team/community, versionamento, riuso multi-progetto |

Il manifest (`.claude-plugin/plugin.json`) è **opzionale**: se assente, Claude Code auto-scopre i componenti nelle location di default e deriva il nome del plugin dal nome della directory.

### 1.2 Struttura directory standard

```
enterprise-plugin/
├── .claude-plugin/           # SOLO qui va plugin.json — mai altro
│   └── plugin.json
├── skills/                   # skill: <name>/SKILL.md
│   ├── code-reviewer/SKILL.md
│   └── pdf-processor/{SKILL.md, scripts/}
├── commands/                 # skill come .md flat (legacy, preferire skills/)
├── agents/                   # subagenti (.md)
├── workflows/                # script di workflow
├── output-styles/            # output style
├── themes/                   # temi colore
├── monitors/monitors.json    # monitor in background
├── hooks/hooks.json          # hook
├── bin/                      # eseguibili aggiunti al PATH del tool Bash
├── settings.json             # default settings (solo chiavi "agent" e "subagentStatusLine")
├── .mcp.json                 # server MCP
├── .lsp.json                 # server LSP
├── scripts/
├── LICENSE
└── CHANGELOG.md
```

**Errore comune**: mettere `commands/`, `agents/`, `skills/`, `hooks/` dentro `.claude-plugin/`. Devono stare alla radice del plugin. La plugin root non è mai `~/.claude/` — un `.mcp.json` in `~/.claude/.mcp.json` non viene letto.

Un `CLAUDE.md` alla radice del plugin **non** viene caricato come contesto di progetto — i plugin veicolano istruzioni tramite skill/agenti/hook.

Un plugin con **un solo skill** può mettere `SKILL.md` direttamente alla radice, senza directory `skills/`.

### 1.3 Schema completo di `.claude-plugin/plugin.json`

```jsonc
{
  // ── Identità (solo "name" è obbligatorio se il manifest esiste) ──
  "name": "plugin-name",                  // kebab-case, namespace di skill/agenti
  "displayName": "Plugin Name",           // v2.1.143+, label UI, può avere spazi
  "version": "1.2.0",                     // vedi § 1.6 versionamento
  "description": "Brief plugin description",
  "author": {
    "name": "Author Name",                // unico campo obbligatorio dentro author
    "email": "author@example.com",
    "url": "https://github.com/author"
  },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",                       // identificatore SPDX
  "keywords": ["keyword1", "keyword2"],
  "metadata": { "catalogId": "cat-123" }, // free-form, MAI letto da Claude Code
  "defaultEnabled": false,                // v2.1.154+, installa disabilitato

  // ── Path componenti (sovrascrivono o estendono le location di default) ──
  "skills": "./custom/skills/",           // string|array — SI SOMMA a skills/ di default
  "commands": ["./custom/commands/special.md"], // string|array — SOSTITUISCE commands/
  "agents": ["./custom/agents/reviewer.md"],    // string|array — SOSTITUISCE agents/
  "workflows": "./custom/workflows/",     // SOSTITUISCE workflows/
  "hooks": "./config/hooks.json",         // string|array|object
  "mcpServers": "./mcp-config.json",      // string|array|object
  "outputStyles": "./styles/",            // SOSTITUISCE output-styles/
  "lspServers": "./.lsp.json",            // string|array|object

  // ── Componenti sperimentali (schema instabile) ──
  "experimental": {
    "themes": "./themes/",
    "monitors": "./monitors.json"
  },

  // ── Dipendenze da altri plugin ──
  "dependencies": [
    "helper-lib",
    { "name": "secrets-vault", "version": "~2.1.0" }
  ],

  // ── Configurazione utente richiesta all'enable ──
  "userConfig": {
    "api_endpoint": { "type": "string", "title": "API endpoint", "description": "..." },
    "api_token": { "type": "string", "title": "API token", "description": "...", "sensitive": true }
  },

  // ── Canali di messaggistica (Telegram/Slack/Discord-style) ──
  "channels": [
    { "server": "telegram", "userConfig": { "bot_token": { "type": "string", "title": "...", "description": "...", "sensitive": true } } }
  ]
}
```

**Campi ignorati senza errore**: qualunque campo top-level non riconosciuto viene ignorato silenziosamente — permette a `plugin.json` di raddoppiare come `package.json` npm, manifest VS Code/Cursor o bundle MCPB/DXT. `claude plugin validate` segnala i campi sconosciuti solo come warning (errore solo con `--strict`).

**Tipizzazione**: se un campo riconosciuto ha il tipo sbagliato (es. `keywords` come stringa invece di array) il plugin **non carica** — eccetto `experimental` e `metadata`, che se non-oggetto vengono semplicemente ignorati con warning.

#### Campo `userConfig` — dettaglio opzioni

| Campo | Obbligatorio | Descrizione |
|---|---|---|
| `type` | Sì | `string`, `number`, `boolean`, `directory`, `file` |
| `title` | Sì | Label nel dialog di configurazione |
| `description` | Sì | Testo di aiuto |
| `sensitive` | No | Se `true`, maschera l'input e salva in secure storage (Keychain macOS o `~/.claude/.credentials.json`) invece che in `settings.json` |
| `required` | No | Fallisce validazione se vuoto |
| `default` | No | Valore di default |
| `multiple` | No | Per `string`, consente array |
| `min`/`max` | No | Bound per `number` |

I valori non-sensitive vanno in `pluginConfigs[<plugin-id>].options` dentro `~/.claude/settings.json` (utente). I valori sensitive vanno in Keychain (limite ~2KB totali, condiviso con OAuth token). `pluginConfigs` viene letto **solo** da: user settings, flag `--settings`/SDK, managed settings — **mai** da `.claude/settings.json` o `.claude/settings.local.json` di progetto (per evitare che un repo clonato inietti valori tramite hook/MCP/LSP).

### 1.4 Variabili d'ambiente per path

| Variabile | Risolve a | Uso |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | Path assoluto della directory di installazione del plugin (cambia a ogni update) | Script, binari, config bundlati col plugin |
| `${CLAUDE_PLUGIN_DATA}` | `~/.claude/plugins/data/{id}/` — directory persistente che sopravvive agli update, creata al primo riferimento | `node_modules`, venv Python, cache, codice generato |
| `${CLAUDE_PROJECT_DIR}` | Root del progetto | Script/config del progetto |

`{id}` = identificatore plugin con caratteri fuori da `a-z A-Z 0-9 _ -` sostituiti da `-` (es. `formatter@my-marketplace` → `~/.claude/plugins/data/formatter-my-marketplace/`).

Sostituzione per componente:

| Componente | Campi dove il placeholder si risolve |
|---|---|
| Skill/agent content | ovunque |
| Hook e monitor commands | ovunque |
| MCP stdio servers | `command`, `args`, `env` |
| MCP http/sse/ws servers | `url`, `headers`, `headersHelper` |
| LSP servers | `command`, `args`, `env`, `workspaceFolder` |

`${user_config.*}` **non** si sostituisce in campi che passano per una shell (hook shell-form, comandi monitor, MCP `headersHelper`) — per sicurezza (iniezione shell). Alternative: exec-form con `args`, oppure lettura di `CLAUDE_PLUGIN_OPTION_<KEY>` dall'ambiente del processo.

### 1.5 Cache e risoluzione file

I plugin installati da marketplace vengono **copiati** in `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` — non usati in-place. Conseguenze:

- **Niente path traversal**: `../shared-utils` non funziona dopo l'installazione (il file esterno non viene copiato).
- **Symlink**: dentro la propria directory → preservati come symlink relativi; altrove nello stesso marketplace → dereferenziati (contenuto copiato); fuori dal marketplace → **saltati** per sicurezza.
- **Versioni orfane**: quando un plugin viene aggiornato/disinstallato, la directory della vecchia versione resta marcata orfana e viene rimossa **14 giorni dopo** (grace period per sessioni concorrenti già caricate). Glob/Grep di Claude saltano le directory orfane.
- **Marker `.in_use/<pid>`**: file vuoti nominati con il PID del processo che sta usando quella versione della cache — meccanismo di riferimento per capire quando una versione può essere ripulita. Verificato su disco: `.in_use/66942`, `.in_use/57453`, ecc.
- **`.orphaned_at`**: marker di timestamp per versioni segnate come orfane (verificato su disco in `claude-mem/13.13.0/.orphaned_at`).
- **`.last_inuse_sweep`**: file a livello `~/.claude/plugins/` con timestamp dell'ultima pulizia (verificato: `2026-08-06T12:39:20.806Z`).

### 1.6 Versionamento e risoluzione versione

Ordine di risoluzione (primo che è settato vince):

1. `version` in `plugin.json` del plugin
2. `version` nell'entry del plugin dentro `marketplace.json`
3. Git commit SHA della source del plugin (per source `github`, `url`, `git-subdir`, o path relativo dentro un marketplace git-hosted)
4. `"unknown"` per source `npm` o directory locali fuori da un repo git

**Attenzione**: se `version` è settato in `plugin.json`, va **bumpato a ogni release** — nuovi commit senza bump del campo non fanno nulla per gli utenti esistenti (`/plugin update` risponde "already at the latest version"). Se si omette `version`, ogni nuovo commit conta come nuova versione (comodo per plugin interni/in sviluppo attivo). **Non settare `version` sia in `plugin.json` sia nell'entry marketplace**: `plugin.json` vince sempre senza warning, mascherando silenziosamente il valore del marketplace.

Verificato su disco: `claude-mem` ha 4 directory di versione coesistenti nella cache (`13.13.1`, `13.13.0`, `13.12.4`, `13.12.2`) — conferma diretta del meccanismo multi-versione.

### 1.7 Scope di installazione

| Scope | File di destinazione | Uso |
|---|---|---|
| `user` (default) | `~/.claude/settings.json` → chiave `enabledPlugins` | Plugin personali, disponibili in tutti i progetti |
| `project` | `.claude/settings.json` | Plugin di team, condivisi via version control |
| `local` | `.claude/settings.local.json` | Plugin specifici del progetto, gitignored |
| `managed` | Managed settings (read-only) | Plugin gestiti da amministratore |

`enabledPlugins` è un **oggetto**, non un array (verificato in ground-truth `~/.claude/settings.json`):

```json
"enabledPlugins": {
  "feature-dev@claude-plugins-official": true,
  "test-driver@l3digitalnet-plugins": true,
  "claude-mem@thedotmack": true
}
```

Chiave = `<plugin-name>@<marketplace-name>` (il `plugin-name` è quello dell'**entry di marketplace**, che può differire dal `name` interno di `plugin.json`).

### 1.8 Plugin da skills-directory (senza marketplace)

Qualunque cartella sotto una directory di skill che contiene `.claude-plugin/plugin.json` viene caricata come plugin `<name>@skills-dir` alla sessione successiva — **niente marketplace, niente install step**. Scaffolding: `claude plugin init <name>` → crea `~/.claude/skills/<name>/`.

| Skills directory | Scope | Carica |
|---|---|---|
| `~/.claude/skills/` | personale | in ogni progetto |
| `<cwd>/.claude/skills/` | progetto | solo dopo trust dialog per quella cartella |

Un plugin project-scope `@skills-dir` **non risale** alla root del repo come fanno skill/comandi normali — carica solo da `.claude/skills/` della directory di avvio.

### 1.9 Componenti in dettaglio

**Skill**: `skills/<name>/SKILL.md` (nuovo formato) o `commands/<name>.md` (flat, legacy). Frontmatter booleano (`disable-model-invocation`) accetta `yes/no/on/off/1/0` oltre a `true/false` (v2.1.218+).

**Agenti**: `agents/*.md`. Frontmatter supportato: `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation` (solo valore valido: `"worktree"`). **Non supportati** per sicurezza: `hooks`, `mcpServers`, `permissionMode`.

**Hook**: `hooks/hooks.json`, stessi eventi degli hook utente (elenco completo: `SessionStart`, `Setup`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Notification`, `MessageDisplay`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `Stop`, `StopFailure`, `TeammateIdle`, `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Elicitation`, `ElicitationResult`, `SessionEnd`). Tipi di hook: `command`, `http`, `mcp_tool`, `prompt`, `agent`.

**MCP server**: `.mcp.json` alla radice o inline in `plugin.json` via `mcpServers`. Si avviano automaticamente quando il plugin è enabled. Nome scoped: `plugin:<plugin-name>:<server-name>`; i tool appaiono come `mcp__plugin_<plugin-name>_<server-name>__<tool>`.

**LSP server**: `.lsp.json` o `lspServers` inline. Campi obbligatori: `command`, `extensionToLanguage`. Opzionali: `args`, `transport` (`stdio`|`socket`), `env`, `initializationOptions`, `settings`, `workspaceFolder`, `startupTimeout`, `shutdownTimeout`, `restartOnCrash` (default `true`), `maxRestarts`, `diagnostics` (default `true`). Se più server dichiarano la stessa estensione, vince il primo registrato. Plugin LSP ufficiali verificati: `rust-analyzer-lsp` (installato su questa macchina, versione `1.0.0`, **senza alcun file oltre a `.in_use/`** — plugin puramente dichiarativo, tutto definito nell'entry di marketplace con `strict: false`).

**Monitor**: `monitors/monitors.json`, processi persistenti in background che inviano ogni riga di stdout come notifica. Campi: `name`, `command` (obbligatori), `description`, `when` (`"always"` default, o `"on-skill-invoke:<skill-name>"`). Girano solo in sessioni CLI interattive, non sandboxati, stesso livello di trust degli hook.

**Temi**: `themes/*.json` con `base` (`dark`/`light`) e `overrides` (mappa token colore). Read-only per l'utente finché non li copia in `~/.claude/themes/`.

**Settings di default del plugin**: `settings.json` alla radice del plugin — supporta **solo** le chiavi `agent` (attiva un agente del plugin come thread principale) e `subagentStatusLine`. Priorità: `settings.json` del plugin > `settings` dichiarato in `plugin.json`.

**Eseguibili**: `bin/` → aggiunti al `PATH` del tool Bash mentre il plugin è enabled, invocabili come comando nudo.

---

## 2. Marketplace

### 2.1 Cos'è e come si crea

Un marketplace è un catalogo (`marketplace.json`) che elenca plugin e le loro source. Va creato in `.claude-plugin/marketplace.json` alla radice di un repo.

```json
{
  "name": "company-tools",
  "owner": { "name": "DevTools Team", "email": "devtools@example.com" },
  "plugins": [
    {
      "name": "code-formatter",
      "source": "./plugins/formatter",
      "description": "Automatic code formatting on save",
      "version": "2.1.0",
      "author": { "name": "DevTools Team" }
    },
    {
      "name": "deployment-tools",
      "source": { "source": "github", "repo": "company/deploy-plugin" },
      "description": "Deployment automation tools"
    }
  ]
}
```

### 2.2 Schema completo di `marketplace.json`

**Campi obbligatori top-level:**

| Campo | Tipo | Descrizione |
|---|---|---|
| `name` | string | Identificatore kebab-case, pubblico (`/plugin install my-tool@your-marketplace`). Un utente può registrare **un solo marketplace per nome** — un secondo add con lo stesso nome sostituisce il primo |
| `owner` | object | `{name (oblig.), email?, url?}` |
| `plugins` | array | Lista di plugin entry |

**Nomi riservati** (bloccati per marketplace di terze parti): `claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `claude-plugins-community`, `claude-community`, `anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, `anthropic-agent-skills`, `knowledge-work-plugins`, `life-sciences`, `claude-for-legal`, `claude-for-financial-services`, `financial-services-plugins`, `first-party-plugins`, `healthcare` — più qualunque nome che impersoni marketplace ufficiali (`official-claude-plugins`, `anthropic-plugins-v2`). Il check viene rifatto **a ogni load**, non solo all'add.

**Campi facoltativi top-level:**

| Campo | Tipo | Descrizione |
|---|---|---|
| `$schema` | string | URL JSON Schema (ignorato al load) |
| `description` | string | Descrizione breve |
| `version` | string | Versione del manifest marketplace |
| `metadata.pluginRoot` | string | Directory base prependuta ai path relativi (`"./plugins"` → si scrive `"source": "formatter"` invece di `"./plugins/formatter"`) |
| `allowCrossMarketplaceDependenciesOn` | array | Altri marketplace da cui i plugin di questo marketplace possono dipendere |
| `renames` | object | Mappa vecchio-nome → nuovo-nome (o `null` se rimosso), per migrazione automatica (richiede v2.1.193+) |

`description` e `version` sono accettati anche dentro `metadata` per retrocompatibilità.

**Ground-truth**: il marketplace ECC locale (`~/.claude/marketplace.json`) usa lo schema con `owner{name,email}`, `metadata.description`, e un array `plugins` con campi extra non-standard come `homepage`, `repository`, `license`, `category`, `tags`, `strict: false` — dimostrando che il marketplace entry accetta *qualunque campo del plugin manifest schema* oltre ai campi marketplace-specifici.

### 2.3 Plugin entry — campi

**Obbligatori**: `name` (string, kebab-case), `source` (string|object).

**Metadata standard** (ereditati dallo schema di `plugin.json`): `displayName`, `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `metadata`.

**Marketplace-specifici**:

| Campo | Tipo | Descrizione |
|---|---|---|
| `category` | string | Categoria per organizzazione (es. `security`, `productivity`, `development`) |
| `tags` | array | Tag per ricerca |
| `strict` | boolean (default `true`) | Vedi § 2.5 |
| `relevance` | object | Segnali per suggerimenti contestuali (richiede allowlist admin via managed settings, v2.1.152+) |
| `defaultEnabled` | boolean | Sovrascrive lo stesso campo in `plugin.json` (v2.1.154+) |

**Path componenti** (sovrascrivono/estendono come in `plugin.json`): `skills`, `commands`, `agents`, `hooks`, `mcpServers`, `lspServers`.

### 2.4 Source dei plugin (`source` field)

| Source | Forma | Campi | Note |
|---|---|---|---|
| Path relativo | `"./my-plugin"` (string) | — | Deve iniziare con `./`. Risolto relativo alla **marketplace root** (dir contenente `.claude-plugin/`), non a `.claude-plugin/` stesso. Non ammesso `../` |
| `github` | object | `repo` (oblig.), `ref?`, `sha?` | `repo` = `owner/repo` |
| `url` | object | `url` (oblig.), `ref?`, `sha?` | Git URL generico (`https://` o `git@`), suffisso `.git` opzionale |
| `git-subdir` | object | `url` (oblig.), `path` (oblig.), `ref?`, `sha?` | Sparse/partial clone di una subdirectory — ottimo per monorepo |
| `npm` | object | `package` (oblig.), `version?`, `registry?` | Installato via `npm install` |

Quando sono settati sia `ref` sia `sha`, **`sha` è il pin effettivo**. Su GitHub/GitLab/Bitbucket funziona anche se il branch/tag di `ref` è stato cancellato, purché il commit sia ancora raggiungibile. Server come AWS CodeCommit non supportano fetch per SHA: lì `ref` deve ancora esistere.

**Marketplace source ≠ plugin source**: il *marketplace source* dice dove scaricare `marketplace.json` (settato con `/plugin marketplace add` o `extraKnownMarketplaces`, supporta `ref` ma non `sha`); il *plugin source* dice dove scaricare il singolo plugin elencato (settato nel campo `source` dell'entry, supporta sia `ref` sia `sha`). Sono pinnati indipendentemente.

**Distribuzione via Organization settings > Plugins** (Team/Enterprise): regole diverse — il repo del marketplace dev'essere privato/interno; solo source `github`/`url`/`git-subdir` (niente `npm`); un plugin source può essere privato solo se condivide l'owner del repo marketplace su github.com, o è su GitHub Enterprise con la GHE App installata.

**Ground-truth verificata**: `claude-plugins-official/.claude-plugin/marketplace.json` contiene 278 plugin con `source` nei formati `string` (path relativo), `{"source": "github", ...}`, `{"source": "url", ...}`, `{"source": "git-subdir", ...}` — tutti e 4 confermati sul campo.

### 2.5 Strict mode

Il campo `strict` controlla se `plugin.json` è l'autorità sui componenti dichiarati:

| Valore | Comportamento |
|---|---|
| `true` (default) | `plugin.json` è l'autorità. L'entry di marketplace può **aggiungere** componenti extra, e le due fonti vengono unite |
| `false` | L'entry di marketplace è la definizione **completa**. Se il plugin ha anche un `plugin.json` che dichiara componenti, è un conflitto e il plugin non carica |

Uso tipico di `strict: false`: il marketplace vuole controllo pieno e il repo del plugin fornisce solo file raw (es. `rust-analyzer-lsp`, verificato in ground-truth: nessun `plugin.json` nella cache, tutto definito nell'entry marketplace con `lspServers` inline).

### 2.6 Comandi CLI/slash

| Comando | Effetto |
|---|---|
| `/plugin marketplace add <source>` | Aggiunge un marketplace: GitHub `owner/repo`[`@ref`], git URL[`#ref`], path locale, URL diretto a `marketplace.json` |
| `claude plugin marketplace add <source> [--scope user\|project\|local] [--sparse <paths...>]` | Versione CLI non-interattiva |
| `/plugin marketplace list` / `claude plugin marketplace list [--json]` | Elenca marketplace configurati |
| `/plugin marketplace update [name]` | Aggiorna dal source (omesso = tutti) |
| `/plugin marketplace remove <name> [--scope ...]` | Rimuove — **disinstalla anche i plugin** se è l'ultimo scope in cui era dichiarato |
| `/plugin install <plugin>@<marketplace>` | Apre dettaglio e scelta scope |
| `claude plugin install <plugin> [-s user\|project\|local] [--config k=v]` | Versione CLI |
| `claude plugin uninstall/remove/rm <plugin> [--keep-data] [--prune]` | Disinstalla |
| `claude plugin enable/disable <plugin> [-s scope]` | Abilita/disabilita senza disinstallare |
| `claude plugin update <plugin> [-s scope]` | Aggiorna |
| `claude plugin list [--json] [--available]` | Elenco |
| `claude plugin details <name>` | Inventario componenti + costo token stimato (always-on vs on-invoke) |
| `claude plugin validate <path> [--strict]` | Valida `marketplace.json`/`plugin.json` |
| `claude plugin init <name> [--with skills agents hooks mcp lsp output-style channel]` | Scaffold in `~/.claude/skills/<name>/` (plugin `@skills-dir`, no marketplace) |
| `claude plugin tag [path] [--push] [--dry-run]` | Crea git tag di release |
| `/reload-plugins [--force]` | Applica modifiche senza restart |

### 2.7 `known_marketplaces.json` vs `extraKnownMarketplaces`

**`~/.claude/plugins/known_marketplaces.json`** — stato **locale, per-utente** (non per-progetto) di tutti i marketplace registrati, scritto da Claude Code quando esegui `/plugin marketplace add`. Formato verificato:

```json
{
  "claude-plugins-official": {
    "source": { "source": "github", "repo": "anthropics/claude-plugins-official" },
    "installLocation": "/home/matt/.claude/plugins/marketplaces/claude-plugins-official",
    "lastUpdated": "2026-08-06T13:48:24.662Z"
  },
  "thedotmack": {
    "source": { "source": "github", "repo": "thedotmack/claude-mem" },
    "installLocation": "/home/matt/.claude/plugins/marketplaces/thedotmack",
    "lastUpdated": "2026-08-06T13:48:25.531Z",
    "autoUpdate": true
  }
}
```

Chiavi: `source`, `installLocation` (path cache locale), `lastUpdated`, `autoUpdate` (opzionale, bool).

**`extraKnownMarketplaces`** — chiave dentro `settings.json` (a **qualunque** scope: user/project/local/managed) che **dichiara** marketplace da registrare automaticamente al trust del progetto. Formato verificato in `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "l3digitalnet-plugins": { "source": { "source": "github", "repo": "L3DigitalNet/Claude-Code-Plugins" } },
    "thedotmack": { "source": { "source": "github", "repo": "thedotmack/claude-mem" } }
  }
}
```

**Relazione**: `known_marketplaces.json` è il registro effettivo/cache (dove i marketplace *sono già* registrati); `extraKnownMarketplaces` in `settings.json` è la **dichiarazione dichiarativa** (spesso committata in `.claude/settings.json` di progetto) che causa la registrazione automatica in `known_marketplaces.json` quando un utente accetta il trust dialog del progetto. Un team admin mette `extraKnownMarketplaces` nel `.claude/settings.json` versionato; ogni collaboratore che clona il repo e fa trust ottiene il marketplace registrato in automatico nel proprio `known_marketplaces.json` locale.

Marketplace state è **per-utente**, non per-progetto: anche eseguendo Claude Code da un git worktree, `known_marketplaces.json` è unico e condiviso.

### 2.8 Marketplace ufficiali e community

| Marketplace | Come si aggiunge | Note |
|---|---|---|
| `claude-plugins-official` | Automatico al primo avvio interattivo | Curato da Anthropic, nessun processo di application |
| `claude-community` (repo `anthropics/claude-plugins-community`) | `/plugin marketplace add anthropics/claude-plugins-community` | Submission di terze parti dopo review automatica; ogni plugin pinnato a uno SHA specifico, sync notturno |
| `claude-code-plugins` (demo, repo `anthropics/claude-code`) | `/plugin marketplace add anthropics/claude-code` | Plugin di esempio |

Sottomissione al community marketplace: form in-app su claude.ai (richiede org Team/Enterprise) o `platform.claude.com/plugins/submit` (autori individuali). `claude plugin validate ./your-plugin` gira in locale prima della submission — la review pipeline esegue lo stesso check + safety screening automatico.

### 2.9 Restrizioni enterprise sui marketplace

`strictKnownMarketplaces` (solo **managed settings**) controlla quali marketplace gli utenti possono aggiungere:

| Valore | Comportamento |
|---|---|
| non definito (default) | nessuna restrizione |
| `[]` | lockdown totale, blocca anche il marketplace ufficiale |
| lista di source | whitelist esatta (match esatto su `repo`+`ref`+`path`, o `hostPattern`/`pathPattern` regex) |

`blockedMarketplaces` (denylist) ha sempre precedenza sulle whitelist. Le restrizioni sono controllate **prima** di qualunque operazione di rete/filesystem, sia su add sia su install/update/refresh/auto-update.

---

## 3. Mappa completa dei file di configurazione

### 3.1 Tabella esaustiva

| Livello | File | Path esatto | Scope | Versionato? |
|---|---|---|---|---|
| **Enterprise/Managed** | `managed-settings.json` | macOS: `/Library/Application Support/ClaudeCode/managed-settings.json` · Linux/WSL: `/etc/claude-code/managed-settings.json` · Windows: `C:\Program Files\ClaudeCode\managed-settings.json` | Enterprise (massima priorità) | No (deployment via MDM/plist/registry) |
| **Enterprise/Managed** | `managed-settings.d/*.json` | stessa dir del file base | Enterprise, drop-in | No — merge alfabetico, ultimo vince su scalari |
| **Enterprise/Managed** | `managed-mcp.json` | stessa dir sistema | MCP a livello enterprise | No |
| **Utente** | `settings.json` | `~/.claude/settings.json` (Win: `%USERPROFILE%\.claude\settings.json`) | Utente, tutti i progetti | No (personale) |
| **Utente** | `.claude.json` | `~/.claude.json` (mode 600) | Stato client/telemetria + registro MCP globale (`mcpServers`) + stato per-progetto (`projects`) | No |
| **Utente** | `CLAUDE.md` | `~/.claude/CLAUDE.md` | Memoria utente, iniettata in ogni progetto | No |
| **Utente** | `agents/` | `~/.claude/agents/` | Subagenti personali | No |
| **Utente** | `skills/` | `~/.claude/skills/` | Skill personali (anche plugin `@skills-dir`) | No |
| **Utente** | `themes/` | `~/.claude/themes/` | Temi personali/copie editabili di temi plugin | No |
| **Utente** | `.credentials.json` | `~/.claude/.credentials.json` | Fallback secure storage (no Keychain disponibile) | No |
| **Utente/Plugin** | `installed_plugins.json` | `~/.claude/plugins/installed_plugins.json` | Registro plugin installati (`{version, plugins: {"<name>@<marketplace>": [...]}}`) | No |
| **Utente/Plugin** | `known_marketplaces.json` | `~/.claude/plugins/known_marketplaces.json` | Registro marketplace registrati | No |
| **Utente/Plugin** | `marketplaces/<name>/` | `~/.claude/plugins/marketplaces/<name>/` | Clone completo del repo marketplace | No |
| **Utente/Plugin** | `cache/<marketplace>/<plugin>/<version>/` | `~/.claude/plugins/cache/...` | Copia installata del plugin (per versione) | No |
| **Utente/Plugin** | `data/<plugin-id>/` | `~/.claude/plugins/data/...` | `${CLAUDE_PLUGIN_DATA}`, persistente tra update | No |
| **Progetto** | `settings.json` | `.claude/settings.json` | Team, condiviso | **Sì**, committato |
| **Progetto** | `settings.local.json` | `.claude/settings.local.json` | Override personali di progetto | No — auto-aggiunto a `core.excludesFile` |
| **Progetto** | `CLAUDE.md` | `CLAUDE.md` o `.claude/CLAUDE.md` (root repo) | Memoria di progetto | **Sì** |
| **Progetto** | `CLAUDE.local.md` | `.claude/CLAUDE.local.md` | Memoria locale personale | No |
| **Progetto** | `.mcp.json` | `<root-progetto>/.mcp.json` | Server MCP di progetto (project-scope) | **Sì** |
| **Progetto** | `agents/` | `.claude/agents/` | Subagenti di progetto | **Sì** |
| **Progetto** | `skills/` | `.claude/skills/` | Skill di progetto (anche plugin `@skills-dir` project-scope) | **Sì** |
| **Progetto** | `rules/*.md` | `.claude/rules/**/*.md` | Regole caricate come istruzioni (hook `InstructionsLoaded`) | **Sì** |
| **Plugin (bundled)** | `plugin.json` | `<plugin-root>/.claude-plugin/plugin.json` | Manifest | — |
| **Plugin (bundled)** | `settings.json` | `<plugin-root>/settings.json` | Default settings plugin (solo `agent`, `subagentStatusLine`) | — |
| **Plugin (bundled)** | `.mcp.json` | `<plugin-root>/.mcp.json` | MCP del plugin | — |

### 3.2 Precedenza tra file di settings (`settings.json`)

Ordine di priorità (dal più alto al più basso):

1. **Managed** (`managed-settings.json` + drop-in) — non sovrascrivibile, salvo eccezioni esplicite documentate per singolo campo
2. **Argomenti CLI** (override di sessione temporanei)
3. **Local** (`.claude/settings.local.json`)
4. **Project** (`.claude/settings.json`)
5. **User** (`~/.claude/settings.json`)

**Regola generale**: per impostazioni scalari/array standard vale l'override puro (vince il file a priorità più alta).

**Eccezione — `permissions`**: `allow`, `ask`, `deny` si **fondono** (merge) attraverso tutti gli scope invece di sovrascriversi. Un valore restrittivo da managed settings ha comunque precedenza. Le regole `allow` in `.claude/settings.local.json` hanno effetto **senza richiedere il trust dialog della workspace**; se invece è il repository stesso a fornire `.claude/settings.local.json` (caso anomalo/committato), il trust dialog si applica comunque.

**Altre non-merge note** (verificate da fonte primaria):

| Chiave | Comportamento |
|---|---|
| `fallbackModel` | NON si fonde — il file a priorità più alta definisce l'intera catena (max 3 modelli) |
| `autoMode` | non letto da project/local (solo user/managed), dal v2.1.207 |
| `claudeMd` | letto **solo** da managed settings — ignorato ovunque altro |
| `claudeMdExcludes` | si applica solo a memoria user/project/local (managed escluso) |
| `askUserQuestionTimeout` | letto solo da user settings |
| `pluginConfigs` | letto solo da user settings + `--settings`/SDK + managed — **mai** da project/local (per evitare iniezione da repo clonato) |
| `enabledPlugins` | fonde attraverso user/project/local/managed |
| `disableClaudeAiConnectors` | semantica "any-source-true": `true` in una sorgente qualsiasi vince, un `false` a priorità più bassa non riabilita |

### 3.3 Il bug/comportamento non-additivo di `settings.local.json`

**Comportamento documentato ufficialmente**: `.claude/settings.local.json` si risolve alla **root del repository** (attraverso i worktree), coprendo tutte le sottodirectory. Prima della v2.1.211 viveva nella directory di avvio; i file legacy in quella posizione restano leggibili.

**Quirk di merge non-additivo**: quando esistono **sia** la copia a root-repo **sia** una copia legacy nella directory di avvio:
- le regole `allow` dei permessi da **entrambi** i file restano in vigore (queste sì si sommano)
- per **tutte le altre chiavi**, vince il valore del file a root-repo — **non è un merge completo**

Workaround: eliminare la copia legacy in sottodirectory, mantenere solo quella a root-repo.

### 3.4 Managed settings — tolleranza di parsing

- **Managed settings**: parsing tollerante — voci invalide vengono scartate silenziosamente, quelle valide restano applicate (un singolo typo non disabilita l'intera policy). `claude doctor` elenca le voci scartate.
- **User/project/local settings**: parsing strict — un errore JSON fa scartare **l'intero file**.
- Campi di enforcement sicurezza hanno gestione per-campo se invalidi: es. `allowedMcpServers` invalido → allowlist vuota (blocco totale); `requiredMinimumVersion`/`requiredMaximumVersion` invalidi → fail open (mai bloccano lo startup).

### 3.5 MCP — file e precedenza (dettaglio, diverso dal resto delle settings)

| Scope MCP | Storage | Condiviso col team | Note |
|---|---|---|---|
| **Local** (default di `claude mcp add`) | `~/.claude.json`, sotto l'entry del progetto corrente | No | Non confondere con "local settings" generali (`.claude/settings.local.json`) — è un concetto distinto |
| **Project** | `.mcp.json` nella root del progetto | Sì, via git | Richiede **approvazione per-server** al primo avvio (`claude mcp reset-project-choices` per resettare le scelte) |
| **User** | `~/.claude.json` (top-level, non sotto un progetto) | No, ma cross-progetto | |
| **Managed** | `managed-mcp.json` (dir sistema) | — | Enterprise |

**Precedenza quando lo stesso nome-server è definito in più posti**: Claude Code si connette **una sola volta**, usando la definizione della source a priorità più alta — **i campi non si fondono tra scope**, vince l'intera entry:

1. Local scope
2. Project scope
3. User scope

Plugin e connector claude.ai fanno match per **endpoint** (stessa URL/comando), non per nome.

`enabledMcpjsonServers` / `disabledMcpjsonServers` (in `settings.json`, qualunque scope) controllano l'**approvazione** dei server dichiarati in `.mcp.json` di progetto — sono un meccanismo distinto da `enabledMcpServers`/`disabledMcpServers` che invece Claude Code scrive automaticamente per-progetto dentro `~/.claude.json` quando l'utente accetta/rifiuta interattivamente. Dal v2.1.196, `enableAllProjectMcpServers`/`enabledMcpjsonServers` committati in `.claude/settings.json` **vengono ignorati in una cartella non fidata** — un repo clonato non può "auto-approvare" i propri server MCP.

### 3.6 `~/.claude.json` — struttura verificata

File da 612+ chiavi top-level, mode `600`. Contiene principalmente stato client/telemetria (`numStartups`, `tipsHistory`, `machineID`, cache vari, ecc.) ma due chiavi sono strutturalmente rilevanti per un control plane:

- **`mcpServers`** — registro MCP a livello globale (server user-scope e i dettagli usati per risolvere la precedenza di § 3.5)
- **`projects`** — oggetto chiave per path-progetto, con stato/telemetria per-progetto:
  ```
  allowedTools, mcpContextUris, mcpServers, enabledMcpjsonServers, disabledMcpjsonServers,
  hasTrustDialogAccepted, projectOnboardingSeenCount, hasClaudeMdExternalIncludesApproved,
  hasClaudeMdExternalIncludesWarningShown, lastGracefulShutdown, lastVersionBase,
  lastCost, lastAPIDuration, lastAPIDurationWithoutRetries, lastToolDuration, lastDuration,
  lastLinesAdded, lastLinesRemoved, lastTotalInputTokens, lastTotalOutputTokens,
  lastTotalCacheCreationInputTokens, lastTotalCacheReadInputTokens, lastTotalWebSearchRequests,
  lastFpsAverage, lastFpsLow1Pct, lastModelUsage, lastSessionId, lastSessionMetrics
  ```
  Da notare: `hasTrustDialogAccepted` per-progetto è la persistenza del trust dialog citato in tutta la doc su MCP/plugin project-scope; `enabledMcpjsonServers`/`disabledMcpjsonServers` esistono **anche qui**, per-progetto, oltre che come chiave di `settings.json`.

### 3.7 `~/.claude/settings.json` — chiavi verificate + rilevanti da fonte primaria

Verificate su questa macchina: `attribution`, `permissions{allow,deny,ask,defaultMode}`, `model`, `hooks` (oggetto per evento, ciascuno con array di `{hooks:[{type,command,timeout,statusMessage,async,once?}]}`), `disableAllHooks`, `statusLine{type,command,padding}`, `enabledPlugins`, `extraKnownMarketplaces`, `spinnerVerbs{mode,verbs}`, `spinnerTipsOverride{excludeDefault,tips}`, `effortLevel`, `tui`, `skipDangerousModePermissionPrompt`, `theme`, `preferredNotifChannel`.

Da fonte primaria, elenco più ampio di chiavi disponibili (selezione rilevante per un control plane):

`env`, `advisorModel`, `agent`, `availableModels`, `enforceAvailableModels`, `fallbackModel`, `editorMode`, `alwaysThinkingEnabled`, `autoCompactEnabled`, `autoCompactWindow`, `autoMemoryEnabled`, `autoMemoryDirectory`, `autoScrollEnabled`, `awaySummaryEnabled`, `askUserQuestionTimeout`, `defaultShell`, `emojiCompletionEnabled`, `spinnerTipsEnabled`, `outputStyle`, `allowedHttpHookUrls`, `allowManagedHooksOnly`, `companyAnnouncements`, `apiKeyHelper`, `awsCredentialExport`, `awsAuthRefresh`, `cleanupPeriodDays`, `autoUpdatesChannel`, `agentPushNotifEnabled`, `disableAgentView`, `disableArtifact`/`enableArtifact`, `disableBundledSkills`, `disableSkillShellExecution`, `disableWorkflows`, `disableAutoMode`, `disableRemoteControl`, `disableDeepLinkRegistration`, `disableClaudeAiConnectors`, `disableSideloadFlags`, `disableBrowserExternalNavigation`, `browserExternalPageTools`, `disableMobileSimulatorTools`, `fastMode`, `autoMode{environment,allow,soft_deny,hard_deny,classifyAllShell}`, `claudeMd`, `claudeMdExcludes`, `channelsEnabled`, `allowedChannelPlugins`, `blockedMarketplaces`, `strictKnownMarketplaces`, `allowedMcpServers`, `deniedMcpServers`, `allowManagedMcpServersOnly`, `enableAllProjectMcpServers`, `enabledMcpjsonServers`, `disabledMcpjsonServers`, `allowAllClaudeAiMcps`, `axScreenReader`, `spinnerAnimationEnabled`, `plugins{<name>:{enabled,config}}`, `pluginConfigs`, `credentialHelpers`, `sandbox{disabled,credentials{files,envVars}}`, `allowManagedPermissionRulesOnly`, `forceLoginOrgUUID`, `requiredMinimumVersion`, `requiredMaximumVersion`.

Schema ufficiale per autocomplete IDE: `"$schema": "https://json.schemastore.org/claude-code-settings.json"` (può essere in ritardo rispetto alle feature più recenti della CLI).

### 3.8 Comandi diagnostici

| Comando | Funzione |
|---|---|
| `/status` | Elenca ogni sorgente di settings caricata (appare solo se carica ≥1 valore valido) |
| `/config [key=value]` | UI a tab per vedere/modificare settings; da v2.1.181 accetta modifica diretta |
| `/doctor` | Elenca voci managed-settings invalide scartate e la relativa sorgente |
| `claude --debug` | Dettaglio caricamento plugin: quali caricano, errori manifest, registrazione skill/agent/hook, init MCP |

---

## 4. Sintesi per il Control Plane

Elementi chiave da rappresentare visivamente:

1. **Grafo Marketplace → Plugin → Componenti**: ogni marketplace (`known_marketplaces.json`) espone N plugin (`marketplace.json.plugins[]`); ogni plugin installato ha una o più versioni in cache (`cache/<mp>/<plugin>/<version>/`), di cui **una sola** è quella "in uso" secondo `installed_plugins.json` + `enabledPlugins`.
2. **Stato enable/disable per scope**: uno stesso plugin può essere enabled a scope diversi (user/project/local/managed) con precedenza — utile una vista a "livelli sovrapposti" simile a CSS specificity.
3. **Origine delle regole di permesso**: dato il merge additivo di `permissions.{allow,deny,ask}` attraverso 4 file, un pannello che mostri **da quale file** proviene ogni singola regola attiva è ad alto valore (replica quello che oggi richiede lettura manuale di 4 JSON).
4. **Timeline versioni plugin**: sfruttare le directory multiple in `cache/<mp>/<plugin>/*` + il meccanismo dei 14 giorni di grace period per mostrare quali versioni sono "vive" vs "in decadimento".
5. **Diff tra `known_marketplaces.json` (registrato) e `extraKnownMarketplaces` (dichiarato in settings, non ancora registrato)** — utile per capire cosa un progetto *vuole* installare vs cosa è *già* installato.
