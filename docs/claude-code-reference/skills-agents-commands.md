# Claude Code — Reference tecnico: Skills, Subagent, Slash command

Documento di reference per lo sviluppo di un "Claude Code Control Plane" (web app locale per gestire Skills, Subagent e Slash command). Ogni claim è verificato contro documentazione ufficiale Anthropic o ground-truth locale reale su questa macchina. Dove un dato non è verificabile con certezza, è segnalato esplicitamente.

Versione riferimento Claude Code al momento della ricerca: ramo `2.1.x` (i numeri di versione citati nel testo, es. "richiede v2.1.198", sono presi verbatim dalla documentazione ufficiale).

---

## Fonti

### Documentazione ufficiale consultata (fetch riuscito)

| Pagina | URL |
|---|---|
| Extend Claude with skills | https://code.claude.com/docs/en/skills |
| Create custom subagents | https://code.claude.com/docs/en/sub-agents |
| Slash Commands in the SDK | https://code.claude.com/docs/en/agent-sdk/slash-commands |
| Plugins reference | https://code.claude.com/docs/en/plugins-reference |
| Commands reference (built-in) | https://code.claude.com/docs/en/commands |

Dominio `docs.claude.com/en/docs/claude-code` (storico): non testato direttamente — le ricerche indicano che il dominio corrente e canonico è `code.claude.com/docs`; `platform.claude.com/docs` esiste in parallelo per Agent Skills lato API/piattaforma (`platform.claude.com/docs/en/agents-and-tools/agent-skills/overview`) ma non è stato usato come fonte primaria qui perché il documento è centrato su Claude Code (CLI), non sulla Skills API generica.

### Ground-truth locale (file letti su questa macchina)

| Percorso | Cosa mostra |
|---|---|
| `~/.claude/skills/research/SKILL.md` | Skill minimale, 2 campi frontmatter, istruzione testuale a lanciare un subagent (non `context: fork`) |
| `~/.claude/skills/handoff/SKILL.md` | `disable-model-invocation: true`, `argument-hint` |
| `~/.claude/skills/dashboard-creator/` | Skill multi-file con `references/` e `assets/` |
| `~/.claude/skills/ios/SKILL.md` | `allowed-tools` in sintassi lista YAML `[Read, Glob, Grep, WebFetch]`, campi custom non standard (`last_verified`, `review_by`, `os_version`) |
| `~/.claude/skills/ios/ui-review/` | Skill annidata con file di reference multipli |
| `/home/matt/Documents/Produzione/junox/.claude/skills/design-taste-frontend-v2/SKILL.md` | Skill di **progetto**, formato cross-tool (agentskills.io-like) con campi extra (`version`, `category`, `tags`, `complexity`, `risk`, `tools`, `source`, `author`, `date_added`) |
| `/home/matt/Documents/Obsidian-Brains/Skills-master/.claude/commands/*.md` | Directory `.claude/commands/` di progetto realmente popolata (formato legacy, >150 file) |
| `~/.claude/agents/code-reviewer.md` | Frontmatter subagent con `tools` in sintassi array YAML |
| `~/.claude/agents/gan-generator.md` | Frontmatter subagent con `color: green` |
| `~/.claude/commands/*.md` | Directory comandi utente-level popolata (es. `code-review.md`, `checkpoint.md`, ecc.) |
| `~/.claude/plugins/cache/claude-plugins-official/code-modernization/unknown/agents/*.md` | Agent bundlati in un plugin |
| `~/.claude/plugins/cache/claude-plugins-official/code-modernization/unknown/commands/*.md` | Command bundlati in un plugin (namespace `code-modernization:*`) |
| `~/.claude/plugins/cache/claude-plugins-official/code-modernization/.claude-plugin/plugin.json` | Manifest plugin minimale (solo `name`, `description`, `author`) |
| `~/.claude/plugins/cache/l3digitalnet-plugins/test-driver/0.6.2/skills/testing-mindset/SKILL.md` | Skill bundlata in plugin **versionato** (manifest con `version`) |
| `~/.claude/plugins/installed_plugins.json` | Formato di registrazione plugin installati (`scope`, `installPath`, `version`, timestamp) |
| `~/.claude/settings.json` | Formato `enabledPlugins` (`"plugin-name@marketplace": true`) |

---

## 1. Skills

### 1.1 Cos'è e dove vive

Una skill è una directory con un file `SKILL.md` (frontmatter YAML + istruzioni Markdown). Claude Code segue lo standard aperto [Agent Skills](https://agentskills.io) ed estende il formato con feature proprie (invocation control, subagent execution, dynamic context injection).

**Cambio strutturale importante (documentato ufficialmente):** *"Custom commands have been merged into skills."* Un file `.claude/commands/deploy.md` e una skill `.claude/skills/deploy/SKILL.md` creano entrambi `/deploy` e funzionano allo stesso modo. `.claude/commands/` resta supportato (formato legacy) ma è **deprecato in favore di** `.claude/skills/`, che aggiunge: cartella per file di supporto, frontmatter di controllo invocazione, caricamento automatico da parte di Claude. Per il control plane questo significa: **Skills e Slash command condividono lo stesso namespace di invocazione** (`/nome`) e in caso di conflitto di nome **la skill vince sul comando legacy**.

### 1.2 Livelli e precedenza

| Livello | Percorso | Ambito |
|---|---|---|
| Enterprise | vedi managed settings | Tutti gli utenti dell'organizzazione |
| Personale | `~/.claude/skills/<nome>/SKILL.md` | Tutti i progetti dell'utente |
| Progetto | `.claude/skills/<nome>/SKILL.md` | Solo il progetto corrente |
| Plugin | `<plugin>/skills/<nome>/SKILL.md` | Dove il plugin è abilitato |

Precedenza a parità di nome: **enterprise > personale > progetto**. Una skill a uno qualsiasi di questi livelli sovrascrive una bundled skill omonima. Le skill di plugin usano namespace `plugin-name:skill-name`, quindi non collidono mai con gli altri livelli.

Le skill di progetto si caricano risalendo da `.claude/skills/` nella directory di lancio fino alla root del repo. Skill in `.claude/skills/` **annidate** sotto sottodirectory si caricano solo quando Claude legge/modifica un file in quella sottodirectory, e se il nome collide con una skill esistente ottengono un nome qualificato dalla directory, es. `apps/web:deploy` (richiede v2.1.203+).

Un simlink `<skill-name>` che punta altrove sul disco viene seguito; se una skill folder contiene anche `.claude-plugin/plugin.json` viene caricata come plugin `<name>@skills-dir` (può quindi bundlare anche agents/hooks/MCP).

**Rilevamento live:** modifiche a `SKILL.md` sotto `~/.claude/skills/`, `.claude/skills/` di progetto o directory aggiunte con `--add-dir` sono rilevate durante la sessione senza restart. Una directory skills **nuova** (che non esisteva all'avvio) richiede restart.

Cowork/cloud sessions (incluse le routine) **non leggono** `~/.claude/skills/` locale — usano le skill abilitate sull'account claude.ai, sincronizzate all'avvio sessione.

### 1.3 Frontmatter — reference completo

```yaml
---
name: my-skill
description: What this skill does
disable-model-invocation: true
allowed-tools: Read Grep
---
```

Tutti i campi sono opzionali; solo `description` è raccomandato (senza, Claude non sa quando applicare la skill).

| Campo | Obbligatorio | Descrizione |
|---|---|---|
| `name` | No | Nome visualizzato negli elenchi. Default: nome directory. Per skill personali/progetto controlla solo l'etichetta, non il comando; per skill di plugin controlla l'ultimo segmento del comando. |
| `description` | Consigliato | Cosa fa e quando usarla. Claude la usa per decidere quando applicare la skill. Se assente, usa il primo paragrafo del Markdown. `description` + `when_to_use` sono troncati a 1.536 caratteri nell'elenco skill. |
| `when_to_use` | No | Contesto aggiuntivo (trigger phrase, esempi). Appeso a `description`, conta nel cap di 1.536 caratteri. |
| `argument-hint` | No | Hint mostrato in autocomplete, es. `[issue-number]` o `[filename] [format]`. |
| `arguments` | No | Argomenti posizionali con nome per sostituzione `$name`. Stringa separata da spazi o lista YAML; i nomi mappano le posizioni in ordine. |
| `disable-model-invocation` | No | `true` = solo l'utente può invocarla (via `/nome`); Claude non la carica mai automaticamente. Impedisce anche il preload nei subagent e l'esecuzione da scheduled task (v2.1.196+). Default `false`. |
| `user-invocable` | No | `false` = nascosta dal menu `/`; solo Claude può invocarla. Default `true`. |
| `allowed-tools` | No | Tool pre-approvati **solo per il turno che invoca la skill**; il grant si azzera al messaggio successivo. Stringa (spazio/virgola) o lista YAML. |
| `disallowed-tools` | No | Tool rimossi dal pool disponibile mentre la skill è attiva. Si azzera al messaggio successivo. |
| `model` | No | Modello attivo mentre la skill è in uso; l'override dura solo il turno corrente. Accetta gli stessi valori di `/model`, o `inherit`. |
| `effort` | No | Effort level (`low`, `medium`, `high`, `xhigh`, `max`) mentre la skill è attiva. |
| `context` | No | `fork` = esegue la skill in un subagent isolato (vedi §1.5). |
| `agent` | No | Tipo di subagent da usare quando `context: fork` è impostato. Default `general-purpose`. |
| `background` | No | Solo con `context: fork`. `false` = attende il risultato nel turno stesso invece che in background (default `true`). Richiede v2.1.218+. |
| `hooks` | No | Hook scoped al ciclo di vita della skill. |
| `paths` | No | Glob pattern che limitano quando la skill si attiva automaticamente (in base ai file su cui si sta lavorando). |
| `shell` | No | `bash` (default) o `powershell`, per i blocchi `` !`command` ``. |
| `metadata` | No | Mappa YAML libera per dati custom (letta da tooling esterno, non da Claude Code). |
| `license` | No | Parte dello standard Agent Skills; Claude Code accetta il campo ma non agisce su di esso. |
| `compatibility` | No | Requisiti ambiente, standard Agent Skills; accettato ma inerte in Claude Code. |

**Booleani:** accettano `yes/no/on/off/1/0` oltre a `true/false` (da v2.1.218; prima solo `true/false`).

**Importante — differenza uso interno vs esterno:** Claude Code accetta *tutti* i campi sopra. Fuori da Claude Code (upload skill su claude.ai, Skills API, `package_skill.py`) sono ammessi **solo** `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`; un campo extra (es. `argument-hint`) causa errore hard alla validazione. Questo spiega perché alcune skill "cross-tool" osservate localmente (es. `design-taste-frontend-v2` in `junox`, con campi come `version`, `category`, `tags`, `complexity`) usano un frontmatter più ampio dello standard: sono pensate per essere lette anche da altri harness, non solo Claude Code, e Claude Code le tollera semplicemente ignorando i campi che non riconosce (comportamento osservato, non documentato esplicitamente come "ignora sempre" per skill native — la doc conferma solo l'errore rigido lato claude.ai/API).

### 1.4 Come Claude decide di invocare una skill

Comportamento di default: **sia l'utente che Claude possono invocare qualunque skill**. L'utente digita `/nome-skill`; Claude la carica automaticamente quando la `description` matcha il contesto della conversazione.

Matrice di controllo:

| Frontmatter | Utente invoca | Claude invoca | Quando entra in contesto |
|---|---|---|---|
| (default) | Sì | Sì | Description sempre in contesto; skill completa al momento dell'invocazione |
| `disable-model-invocation: true` | Sì | No | Description non in contesto; skill completa solo quando l'utente invoca |
| `user-invocable: false` | No | Sì | Description sempre in contesto; skill completa quando invocata |

Pattern per description efficace (da documentazione + esempi reali osservati): la description deve indicare **cosa fa** la skill *e* **quando usarla** — frasi trigger esplicite aiutano il match. Esempio reale locale (`~/.claude/skills/research/SKILL.md`):
> "Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent."

Nota il pattern: prima frase = cosa fa, seconda frase con "Use when..." = trigger.

Il contenuto della skill, una volta caricato, **resta in contesto per il resto della sessione** (non viene ricaricato ad ogni turno); un allowed-tools grant invece si azzera ad ogni messaggio. Se una skill smette di influenzare il comportamento dopo la prima risposta, il contenuto è probabilmente ancora presente ma il modello preferisce altri strumenti — rafforzare `description`/istruzioni, o usare hook per un enforcement deterministico.

**Controllo permessi Skill tool:** `Skill` può essere negato interamente (blocca tutte le skill), oppure regole granulari `Skill(nome)` / `Skill(nome *)` in allow/deny.

### 1.5 Personal vs progetto vs plugin — e skill inline vs subagent dedicato

Non c'è una differenza *strutturale* tra "skill normale" e "skill che lancia un subagent": è controllata dal campo frontmatter `context`.

- **Default (inline):** il body della skill entra nella conversazione principale come istruzioni; Claude esegue lui stesso usando i tool disponibili nella sessione.
- **`context: fork`:** il body della skill diventa il *prompt* di un subagent isolato (senza accesso alla cronologia della conversazione). Il campo `agent` sceglie quale tipo di subagent eseguirla (built-in `Explore`/`Plan`/`general-purpose`, o un subagent custom da `.claude/agents/`). Di default gira **in background** (l'utente continua a lavorare, il risultato arriva a completamento); `background: false` la fa bloccare fino al risultato.

Esempio ufficiale (`deep-research`, `context: fork` + `agent: Explore`) — l'agent Explore/Plan salta CLAUDE.md e git status per restare leggero.

**Osservazione locale rilevante:** la skill `~/.claude/skills/research/SKILL.md` **non** usa `context: fork` nel frontmatter — usa solo testo imperativo nel body ("Spin up a **background agent** to do the research..."), lasciando che sia Claude a decidere di chiamare il tool `Agent` manualmente. Questo è un secondo pattern, informale, per ottenere lo stesso risultato (delega a subagent) senza il meccanismo dichiarativo `context: fork`. Per un control plane è importante distinguere le due modalità: **dichiarativa** (`context: fork` nel frontmatter, verificabile parsando il file) vs **implicita** (istruzione testuale nel body, non rilevabile via frontmatter — richiede analisi del contenuto).

La direzione opposta esiste anche nei subagent: un subagent `.claude/agents/*.md` può avere un campo `skills:` che pre-carica il contenuto completo di skill elencate nel proprio contesto all'avvio (vedi §2.3).

### 1.6 Skill multi-file

```text
my-skill/
├── SKILL.md           # obbligatorio
├── template.md
├── examples/
│   └── sample.md
└── scripts/
    └── validate.sh
```

Solo `SKILL.md` è obbligatorio. Gli altri file vanno **referenziati esplicitamente** dal Markdown di `SKILL.md` (link relativi tipo `[reference.md](reference.md)`) perché Claude sappia cosa contengono e quando caricarli — non vengono letti automaticamente. Raccomandazione ufficiale: `SKILL.md` sotto 500 righe, materiale di reference esteso in file separati.

Esempio reale locale — `~/.claude/skills/dashboard-creator/`:
```
dashboard-creator/
├── SKILL.md
├── references/
│   ├── design_patterns.md
│   └── svg_library.md
└── assets/
    └── templates/
```

Per script eseguibili bundlati, la variabile `${CLAUDE_SKILL_DIR}` risolve alla directory della skill (funziona anche per skill installate a livello personale/progetto/plugin), usabile sia nel body sia nelle regole `allowed-tools`:

```yaml
---
name: render-chart
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/render.sh *)
---
Run `${CLAUDE_SKILL_DIR}/scripts/render.sh <csv-file>` to render the chart.
```

### 1.7 Sostituzioni disponibili nel body

| Variabile | Significato |
|---|---|
| `$ARGUMENTS` | Tutti gli argomenti passati all'invocazione |
| `$ARGUMENTS[N]` | Argomento N-esimo (indice 0-based) |
| `$N` | Scorciatoia per `$ARGUMENTS[N]` (es. `$0`, `$1`) |
| `$name` | Argomento nominato dichiarato in `arguments:` nel frontmatter |
| `${CLAUDE_SESSION_ID}` | ID sessione corrente |
| `${CLAUDE_EFFORT}` | Effort level corrente |
| `${CLAUDE_SKILL_DIR}` | Directory della skill (per plugin, la sottodirectory della skill, non la root del plugin) |
| `${CLAUDE_PROJECT_DIR}` | Root del progetto |

`` !`comando` `` (inline, a inizio riga o dopo whitespace) o blocco fenced `` ```! `` esegue shell **prima** che Claude veda il contenuto — dynamic context injection, non qualcosa che Claude esegue lui stesso.

### 1.8 Tabella riassuntiva — frontmatter Skill

| Campo | Oblig. | Esempio |
|---|---|---|
| `name` | No | `name: deploy` |
| `description` | Consigliato | `description: Deploy the app to production` |
| `when_to_use` | No | `when_to_use: after merging to main` |
| `argument-hint` | No | `argument-hint: [issue-number]` |
| `arguments` | No | `arguments: [issue, branch]` |
| `disable-model-invocation` | No | `disable-model-invocation: true` |
| `user-invocable` | No | `user-invocable: false` |
| `allowed-tools` | No | `allowed-tools: Bash(git add *)` |
| `disallowed-tools` | No | `disallowed-tools: Write, Edit` |
| `model` | No | `model: opus` |
| `effort` | No | `effort: high` |
| `context` | No | `context: fork` |
| `agent` | No | `agent: Explore` |
| `background` | No | `background: false` |
| `hooks` | No | vedi hooks reference |
| `paths` | No | `paths: "*.tsx,*.jsx"` |
| `shell` | No | `shell: powershell` |
| `metadata` | No | `metadata: {tier: pro}` |
| `license` | No | `license: MIT` |
| `compatibility` | No | `compatibility: "requires Node 18+"` |

---

## 2. Subagent / Agenti custom

### 2.1 Cos'è

Un subagent è un file Markdown con frontmatter YAML che gira in una propria context window isolata: system prompt custom, tool ristretti, permessi indipendenti. Claude Code include subagent **built-in** (`Explore`, `Plan`, `general-purpose`, e altri helper) e supporta subagent **custom** definiti dall'utente.

### 2.2 Scope e precedenza

| Location | Scope | Priorità | Come si crea |
|---|---|---|---|
| Managed settings | Organizzazione | 1 (massima) | Deploy via managed settings |
| `--agents` CLI flag | Sessione corrente | 2 | JSON al lancio, non salvato su disco |
| `.claude/agents/` | Progetto corrente | 3 | Chiedi a Claude o crea il file a mano |
| `~/.claude/agents/` | Tutti i progetti utente | 4 | Chiedi a Claude o crea il file a mano |
| `agents/` di un plugin | Dove il plugin è attivo | 5 (minima) | Installato via plugin |

Subagent di progetto si scoprono risalendo da cwd fino alla root repo (ogni `.claude/agents/` intermedia viene scansionata); a parità di `name` tra directory annidate vince quella più vicina alla cwd (v2.1.178+). `~/.claude/agents/` e `.claude/agents/` sono scansionate **ricorsivamente** (si possono organizzare in sottocartelle, es. `agents/review/`), ma il nome del subagent viene **solo** dal campo `name` in frontmatter, non dal path — a parità di `name` nello stesso albero vince l'ordine di lettura filesystem (non documentato deterministicamente); `/doctor` segnala i duplicati.

Per i subagent di **plugin**, una sottocartella dentro `agents/` **diventa parte** dell'identificatore scoped: `agents/review/security.md` in `my-plugin` registra `my-plugin:review:security`.

Subagent di plugin **non supportano** `hooks`, `mcpServers`, `permissionMode` in frontmatter (per motivi di sicurezza) — questi campi vengono ignorati se presenti.

### 2.3 Frontmatter — reference completo

Solo `name` e `description` sono obbligatori.

| Campo | Oblig. | Descrizione |
|---|---|---|
| `name` | **Sì** | Identificatore univoco, lowercase e trattini. Non può contenere `:` (riservato ai namespace di plugin). Passato agli hook come `agent_type`. |
| `description` | **Sì** | Quando Claude deve delegare a questo subagent — è l'hint di routing per l'invocazione automatica. |
| `tools` | No | Lista tool utilizzabili. Se omesso, eredita tutti i tool disponibili ai subagent. Per pre-caricare skill nel contesto, usare `skills`, non elencare `Skill` qui. |
| `disallowedTools` | No | Tool da negare, rimossi dalla lista ereditata o specificata. |
| `model` | No | `sonnet`, `opus`, `haiku`, `fable`, un model ID completo, o `inherit` (default). |
| `permissionMode` | No | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, `manual` (alias di `default`). Ignorato per subagent di plugin. |
| `maxTurns` | No | Numero massimo di turni agentic prima che il subagent si fermi. |
| `skills` | No | Skill da **precaricare per intero** nel contesto all'avvio (non solo la description). Il subagent può comunque invocare skill non elencate via tool Skill, salvo che siano rimosse da `tools`/`disallowedTools`. |
| `mcpServers` | No | Server MCP disponibili al subagent (per nome o definizione inline). Ignorato per subagent di plugin. |
| `hooks` | No | Hook di ciclo di vita scoped al subagent. Ignorato per subagent di plugin. |
| `memory` | No | `user`, `project`, o `local` — scope di memoria persistente cross-sessione. |
| `background` | No | `true` = esegue sempre in background. Se omesso, decide Claude (default: background da v2.1.198). |
| `effort` | No | Effort level (`low`…`max`) mentre il subagent è attivo. |
| `isolation` | No | `worktree` = esegue in un git worktree temporaneo isolato, ripulito automaticamente se il subagent non produce modifiche. **Unico valore documentato per il frontmatter dei subagent** (vedi nota sotto). |
| `color` | No | Colore di visualizzazione: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`. |
| `initialPrompt` | No | Auto-inviato come primo turno utente quando l'agent gira come sessione principale (`--agent`). |

> **Nota su `isolation: remote`.** Il tool `Agent` esposto in alcuni contesti orchestratori (incluso quello con cui è stato generato questo stesso documento) espone un parametro `isolation` con valori enum `worktree` **e** `remote` ("lancia l'agent in un ambiente cloud remoto, gira sempre in background, disponibilità gated"). La documentazione ufficiale di `code.claude.com/docs/en/sub-agents` e `plugins-reference` documenta però **solo** `worktree` come valore valido per il campo `isolation` nel frontmatter `.claude/agents/*.md`. È plausibile che `remote` sia una feature più recente o legata a un layer diverso (background/cloud agents, vedi `/docs/en/agent-view` e `/docs/en/cloud-environments` citati come pagine correlate ma non fetchate in questa ricerca) non ancora documentata nella pagina Subagents consultata. **Da verificare con una release note o con `/docs/en/agent-view` prima di implementarlo nel control plane come valore di frontmatter.**

`--agents` (CLI flag, JSON) accetta lo stesso set di campi via chiavi camelCase equivalenti, più `prompt` al posto del body Markdown.

**Sintassi osservata per `tools` nei file reali locali:** sia stringa comma-separated (`tools: Read, Grep, Glob`, come da esempi ufficiali) sia **lista YAML** (`tools: ["Read", "Grep", "Glob", "Bash"]`, come in `~/.claude/agents/code-reviewer.md` e `~/.claude/agents/gan-generator.md` reali su questa macchina) sono valide.

### 2.4 Subagent built-in

| Agent | Modello | Tool | Scopo |
|---|---|---|---|
| `Explore` | Eredita dalla conversazione (capped a Opus su Claude API) | Solo lettura (Write/Edit negati) | Ricerca/analisi codebase |
| `Plan` | Eredita | Solo lettura | Ricerca durante plan mode |
| `general-purpose` | Eredita | Tutti i tool disponibili ai subagent | Task complessi multi-step con esplorazione + modifica |
| `claude` | Eredita | Tutti i tool | Catch-all quando nessun agent specializzato calza; default per sessioni background dispatchate |
| `statusline-setup` | Sonnet | — | Configurazione statusline (`/statusline`) |
| `claude-code-guide` | Haiku | — | Domande su feature di Claude Code |

`Explore` e `Plan` **saltano** CLAUDE.md e lo snapshot git status della sessione principale (per restare leggeri/economici) — tutti gli altri subagent (built-in e custom) li caricano. Un subagent utente/progetto chiamato `Explore` sovrascrive il built-in e mantiene il proprio campo `model` — quindi impostando `model: haiku` si può forzare Explore su un modello più economico.

### 2.5 Come si invocano

Tre pattern, in scala:

1. **Linguaggio naturale**: nominare il subagent nel prompt ("Use the test-runner subagent to..."); Claude decide se delegare.
2. **@-mention**: `@agent-<nome>` (locale) o `@agent-<plugin>:<nome>` (plugin) — garantisce che *quel* subagent specifico venga usato.
3. **Sessione intera**: `claude --agent <nome>` (o `"agent": "<nome>"` in `.claude/settings.json`) — l'intero thread principale assume il system prompt, i tool e il modello del subagent.

Programmaticamente/dal tool Agent: parametro `subagent_type` seleziona il tipo di agente da lanciare (built-in o custom).

### 2.6 Foreground vs background

- **Foreground:** blocca la conversazione principale finché non finisce; i prompt di permesso passano direttamente all'utente.
- **Background:** gira in parallelo mentre l'utente continua a lavorare; i prompt di permesso emergono nella sessione principale nominando il subagent che li richiede (da v2.1.186).

Da v2.1.198 i subagent girano **in background di default**; Claude sceglie il foreground quando ha bisogno subito del risultato. I subagent in background hanno un **set di tool ridotto** rispetto al foreground (eccetto i fork, che ricevono il pool esatto della conversazione principale): mantengono `Read, Grep, Glob, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage, Artifact` più tutti i tool MCP; ogni altro tool built-in viene rimosso anche se elencato in `tools`.

Il risultato di un subagent in background arriva a Claude come notifica di completamento in un turno successivo; se l'utente chiede lo stato prima, Claude riporta che il subagent è ancora in esecuzione.

### 2.7 Isolation mode: worktree

`isolation: worktree` dà al subagent una copia isolata del repository (git worktree temporaneo), di norma branchata dal branch di default piuttosto che dall'`HEAD` della sessione padre. Il worktree viene ripulito automaticamente se il subagent non produce modifiche. I comandi Bash/PowerShell del subagent girano **dentro** il worktree; un comando la cui working directory risolve fuori (es. verso il checkout principale) fallisce con errore — enforcement di isolamento sia sul working directory sia (per Bash) sul contenuto del comando stesso (blocca redirect git verso il checkout principale).

### 2.8 Utente-definiti vs "di sistema"

| | Subagent custom (`.claude/agents/`, `~/.claude/agents/`) | Subagent built-in (`Explore`, `Plan`, `general-purpose`, `claude`, ecc.) |
|---|---|---|
| Definizione | File Markdown con frontmatter, editabile dall'utente | Predefiniti nel binario Claude Code |
| System prompt | Body del file Markdown | Prompt predefinito, non ispezionabile/editabile |
| Tool | Configurabili via `tools`/`disallowedTools` | Fissi (es. Explore/Plan: solo lettura) |
| Override | — | Un subagent utente con lo **stesso nome** di un built-in (es. `Explore`) lo sovrascrive |
| CLAUDE.md / git status | Caricati sempre | `Explore`/`Plan` li saltano; gli altri built-in li caricano come i custom |

Per bloccare subagent specifici: `permissions.deny: ["Agent(nome)"]` in settings, oppure `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` per rimuovere solo Explore/Plan.

### 2.9 Tabella riassuntiva — frontmatter Subagent

| Campo | Oblig. | Esempio |
|---|---|---|
| `name` | **Sì** | `name: code-reviewer` |
| `description` | **Sì** | `description: Reviews code for quality. Use proactively.` |
| `tools` | No | `tools: Read, Grep, Glob, Bash` oppure `tools: ["Read","Grep"]` |
| `disallowedTools` | No | `disallowedTools: Write, Edit` |
| `model` | No | `model: sonnet` |
| `permissionMode` | No | `permissionMode: acceptEdits` |
| `maxTurns` | No | `maxTurns: 20` |
| `skills` | No | `skills: [api-conventions]` |
| `mcpServers` | No | `mcpServers: [github]` |
| `hooks` | No | vedi hooks reference |
| `memory` | No | `memory: project` |
| `background` | No | `background: true` |
| `effort` | No | `effort: medium` |
| `isolation` | No | `isolation: worktree` |
| `color` | No | `color: green` |
| `initialPrompt` | No | `initialPrompt: "Start reviewing"` |

---

## 3. Slash command

### 3.1 Due formati coesistenti

| | `.claude/commands/*.md` (legacy) | `.claude/skills/<nome>/SKILL.md` (corrente, raccomandato) |
|---|---|---|
| Stato | Ancora funzionante, non deprecato hard, ma la doc raccomanda di migrare | Formato corrente per tutto ciò che prima era "custom command" |
| Nome comando | Nome file senza estensione | Nome directory (o `name` frontmatter per skill di plugin) |
| Directory di supporto | No | Sì (script, reference, esempi) |
| Invocazione automatica da Claude | Sì (comportamento skill-like) | Sì, controllabile con `disable-model-invocation`/`user-invocable` |
| Conflitto di nome con una skill | La skill vince | — |

**Conferma locale del formato legacy tuttora popolato:** `/home/matt/Documents/Obsidian-Brains/Skills-master/.claude/commands/` contiene >150 file `.md` di progetto (namespace `.claude/commands/` di un repo reale), e `~/.claude/commands/` a livello utente contiene decine di comandi (`code-review.md`, `checkpoint.md`, `commit.md`, ecc.) — entrambi i livelli (progetto e personale) sono realmente in uso su questa macchina in parallelo a `~/.claude/skills/`.

### 3.2 Frontmatter (sottoinsieme applicabile ai comandi legacy)

```yaml
---
allowed-tools: Read, Grep, Glob
description: Run security vulnerability scan
model: claude-opus-4-8
argument-hint: [issue-number] [priority]
---
```

I comandi legacy supportano lo stesso frontmatter delle skill (§1.3) essendo stati unificati sotto lo stesso motore; i campi più usati in pratica sono `description`, `allowed-tools`, `model`, `argument-hint`.

### 3.3 Sintassi argomenti

| Sintassi | Significato |
|---|---|
| `$ARGUMENTS` | Intera stringa argomenti passata dopo il nome comando |
| `$ARGUMENTS[N]` | Argomento N-esimo (0-based) |
| `$N` (es. `$0`, `$1`) | Scorciatoia per `$ARGUMENTS[N]` |
| `$name` | Argomento nominato, se dichiarato in `arguments:` (skill) |
| `!`comando`` | Esegue shell **prima** di inviare il contenuto a Claude, sostituendo il placeholder con l'output (git diff, git status, ecc.) |
| `@file` | Include il contenuto di un file nel prompt (es. `@package.json`) |

Placeholder indicizzato senza argomento corrispondente resta letterale nel testo; placeholder nominato senza match si espande a stringa vuota. Argomenti multi-parola richiedono quoting shell-style (`"hello world"`).

Esempio (formato legacy, da documentazione ufficiale):
```markdown
---
argument-hint: [issue-number] [priority]
description: Fix a GitHub issue
---
Fix issue #$0 with priority $1.
```

### 3.4 Namespacing da plugin

I comandi/skill bundlati in un plugin sono invocati come `plugin-name:command-name`. **Verificato localmente**: il plugin `code-modernization` (cache in `~/.claude/plugins/cache/claude-plugins-official/code-modernization/unknown/commands/modernize-map.md`) espone comandi come `/code-modernization:modernize-map`, `/code-modernization:modernize-assess`, ecc. — confermato anche dall'elenco skill disponibili in questa sessione (`code-modernization:modernize-assess`, `code-modernization:modernize-brief`, ...).

Regola generale (skill di plugin): se il plugin ha una sola `SKILL.md` alla root (nessuna directory `skills/`), il nome comando viene dal campo `name` in frontmatter con fallback al nome della directory di installazione (che per i plugin da marketplace è una stringa di versione, es. `unknown` se non pinnata — **confermato localmente**: `plugin.json` di `code-modernization` non ha campo `version`, e il path in cache è infatti `.../code-modernization/unknown/...`).

### 3.5 Comandi built-in principali (non esaustivo)

Distinzione fatta dalla doc ufficiale: comandi **built-in** eseguono logica fissa nel codice CLI; le **bundled skill** (marcate `[Skill]` nel command reference) sono invece prompt-based — istruzioni dettagliate che Claude orchestra con i propri tool. Bundled skill note: `/doctor`, `/code-review`, `/batch`, `/debug`, `/loop`, `/claude-api`, `/dataviz`, `/design-sync`, `/fewer-permission-prompts`, `/verify`, `/run`, `/run-skill-generator`. Sono disattivabili in blocco con `disableBundledSkills` (tranne `/doctor`).

| Comando | Tipo | Scopo |
|---|---|---|
| `/help` | Built-in | Elenco comandi e aiuto |
| `/clear` | Built-in | Reset conversazione a contesto vuoto |
| `/compact [istruzioni]` | Built-in | Riassume la cronologia per liberare contesto |
| `/config` | Built-in | Apre l'interfaccia Settings |
| `/agents` | Built-in | Gestione configurazioni subagent (da v2.1.198 non apre più wizard interattivo: stampa un reminder a editare `.claude/agents/`) |
| `/permissions` | Built-in | Gestione regole di permesso tool |
| `/model [modello]` | Built-in | Cambia modello attivo |
| `/mcp` | Built-in | Gestione connessioni server MCP |
| `/init` | Built-in | Inizializza progetto con CLAUDE.md |
| `/memory` | Built-in | Modifica i file CLAUDE.md di memoria |
| `/context [all]` | Built-in | Visualizza uso del contesto |
| `/cost` / `/usage` | Built-in | Costo/uso della sessione |
| `/hooks` | Built-in | Visualizza configurazioni hook |
| `/add-dir <path>` | Built-in | Aggiunge una directory di lavoro |
| `/fork` / `/subtask` | Built-in | Copia/forka la conversazione in un subagent o sessione background |
| `/background [prompt]` | Built-in | Stacca la sessione come agente in background |
| `/doctor` | Skill (bundled) | Diagnosi setup |
| `/code-review [livello] [--fix]` | Skill (bundled) | Review del diff |
| `/batch <istruzione>` | Skill (bundled) | Orchestrazione di modifiche parallele su larga scala |
| `/debug [descrizione]` | Skill (bundled) | Debug logging e troubleshooting |
| `/loop [intervallo] [prompt]` | Skill (bundled) | Esegue un prompt ripetutamente |
| `/verify` | Skill (bundled) | Build+run per confermare una modifica sull'app reale |
| `/deep-research <domanda>` | Workflow | Fan-out di ricerche web + sintesi report |

L'elenco completo (60+ comandi built-in + skill bundlate) è nella tabella integrale di `/docs/en/commands`; qui è riportato solo un sottoinsieme rappresentativo verificato via fetch.

### 3.6 Tabella riassuntiva — frontmatter comando/skill invocabile

| Campo | Oblig. | Esempio |
|---|---|---|
| `description` | Consigliato | `description: Run security scan` |
| `allowed-tools` | No | `allowed-tools: Bash(git *)` |
| `model` | No | `model: opus` |
| `argument-hint` | No | `argument-hint: [issue-number] [priority]` |
| `disable-model-invocation` | No | `disable-model-invocation: true` (solo per skill, non per `.claude/commands` legacy che non lo supporta come switch dedicato — verificare caso per caso) |

---

## 4. Confronto rapido

| | Skill | Subagent | Slash command (legacy) |
|---|---|---|---|
| Dove vive | `~/.claude/skills/<n>/SKILL.md`, `.claude/skills/<n>/SKILL.md`, `<plugin>/skills/` | `~/.claude/agents/*.md`, `.claude/agents/*.md`, `<plugin>/agents/` | `~/.claude/commands/*.md`, `.claude/commands/*.md`, `<plugin>/commands/` |
| Formato | Directory + `SKILL.md` (frontmatter YAML + Markdown) | Singolo file Markdown (frontmatter YAML + system prompt) | Singolo file Markdown (frontmatter YAML opzionale + testo prompt) |
| Come si invoca | `/nome` (utente) o automatico (Claude, in base a `description`) | Tool `Agent`, linguaggio naturale, `@agent-nome`, `--agent` | `/nome` (utente); testo diventa il prompt |
| Dove gira | Nella conversazione corrente (default) o in subagent isolato (`context: fork`) | Sempre in un contesto isolato proprio (foreground o background) | Nella conversazione corrente (espande a testo prompt) |
| Contenuto | Istruzioni + eventuali file di supporto (script, reference) | System prompt che definisce ruolo/comportamento di un worker | Testo prompt, spesso con `!`comando`` e `@file` per iniettare contesto |
| File multipli | Sì (`scripts/`, `references/`, `examples/`) | No (un solo file) | No (un solo file) |
| Quando usarlo | Procedura/checklist riusabile che deve entrare nel contesto principale, o task da delegare con `context: fork` | Task che produce output verboso da isolare, o che richiede tool ristretti/permessi diversi dalla sessione principale | Scorciatoia rapida per un prompt ricorrente — oggi sostanzialmente sostituito dalle skill |

**Per il control plane:** trattare Skill e Slash command legacy come **due sorgenti dello stesso namespace di comandi invocabili** (`/nome`), con le skill come formato "vincente" e più ricco; i Subagent sono un asse ortogonale — non hanno un comando `/nome` proprio, si raggiungono via delega (tool `Agent`) o `--agent`, e possono essere referenziati *da* una skill (`context: fork` + `agent:`) o referenziare *skill* al proprio interno (campo `skills:` per il preload).

---

## Claim non verificati o incerti

1. **`isolation: remote` per i subagent** — visto nello schema del tool `Agent` disponibile in questo ambiente, ma non documentato in `code.claude.com/docs/en/sub-agents` né in `plugins-reference` (che anzi dice esplicitamente "The only valid `isolation` value is `worktree`" per gli agent di plugin). Da verificare prima di modellarlo nel control plane come valore accettato universalmente nel frontmatter `.claude/agents/*.md`.
2. **Comportamento esatto di `disable-model-invocation` sui comandi legacy `.claude/commands/*.md`** — documentato chiaramente per le skill; per i comandi legacy la doc SDK mostra frontmatter con `allowed-tools`, `description`, `model`, `argument-hint` ma non conferma esplicitamente se `disable-model-invocation`/`user-invocable` si applicano allo stesso modo (probabile, dato che condividono il motore, ma non testato con un fetch dedicato).
3. **Precedenza esatta tra due subagent con lo stesso `name` nella stessa directory** — la doc dice solo "chosen by filesystem read order rather than a documented precedence"; non deterministico, da non affidarci nel control plane per la risoluzione conflitti.
4. **Elenco comandi built-in completo** — la pagina `/docs/en/commands` dichiara "60+ built-in commands"; il fetch ha restituito solo una tabella parziale (troncata a metà alfabeto). L'elenco riportato in §3.5 è un sottoinsieme rappresentativo, non esaustivo — per il control plane sarebbe opportuno un fetch dedicato e completo di quella pagina (con paginazione) prima di costruire una UI che pretenda di enumerare *tutti* i comandi built-in.
5. **Se i campi custom non standard osservati in skill "cross-tool"** (es. `version`, `category`, `tags` in `design-taste-frontend-v2`) vengano silenziosamente ignorati da Claude Code o generino un warning in qualche log — comportamento osservato indirettamente (la skill è presumibilmente funzionante nel progetto) ma non confermato da una riga di documentazione esplicita per skill *native* (la doc conferma solo l'hard error per i path claude.ai/API, non per l'uso nativo in Claude Code).
