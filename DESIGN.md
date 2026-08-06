# DESIGN.md: Claude Code Control Plane

Piano di implementazione ed architettura tecnica: [docs/planning/](docs/planning/README.md). Reference tecnico completo su Claude Code (skill, agenti, hook, MCP, plugin, e l'intera superficie del prodotto): [docs/claude-code-reference/](docs/claude-code-reference/). Ricerche di supporto: [docs/](docs/).

> Questo documento riflette le decisioni prese in una sessione di grilling che ha rivisto sostanzialmente il design iniziale (stack, modello di attivazione, organizzazione). Dove uno storico è utile a capire *perché*, è annotato inline.

## 1. Obiettivo e Scopo del Progetto

Il progetto realizza una **web app locale** per la gestione, configurazione e osservazione visiva/interattiva dell'ambiente Claude Code — non un motore di agenti alternativo, non un IDE.

**Non-goal espliciti:**
- Non è un IDE: nessun editor di codice sorgente, nessuna esecuzione di sessioni Claude Code dentro l'app. La CLI resta lo strumento con cui si scrive/esegue codice.
- Non è un'app nativa: niente Tauri, niente Electron, nessun binario da installare. È una web app servita in locale e aperta nel browser.
- Non è un plugin Claude Code: non si registra come plugin, non passa da marketplace/`.claude-plugin/`. Interagisce con Claude Code leggendo e scrivendo direttamente i file reali che Claude Code stesso legge.
- Non è un processo permanente: nessun demone always-on, nessun autostart di sistema. Si avvia a comando e si spegne da un pulsante nell'app stessa.
- Non si integra con l'account claude.ai: perimetro **filesystem-only** per ora. Funzionalità che vivono lato server Anthropic (Routines, Artifacts, Analytics cloud, Remote Control) restano fuori scope — al più un link esterno, mai un pannello nativo.

**Cosa fa concretamente:**

- Centralizza e semplifica la configurazione di Claude Code, a livello sia globale sia di singolo progetto.
- Cataloga e organizza visivamente tutto ciò che Claude Code può usare: skill, agenti, comandi, server MCP, output style, regole — con una libreria navigabile per cartelle, tag e preferiti.
- Compone visivamente **pacchetti riusabili** (skill + agenti + MCP + regole + prompt) su un canvas a nodi, esportabili e riutilizzabili tra progetti o condivisibili con altri utenti.
- Attiva/disattiva questi pacchetti scrivendo/rimuovendo direttamente i file reali nelle cartelle che Claude Code riconosce nativamente — nessun formato proprietario intermedio da "eseguire".
- Osserva l'attività reale di Claude Code (sessioni, costi, token) e permette di **confrontare** pacchetti/combinazioni di pacchetti sulla base sia della loro composizione sia del loro uso storico effettivo.

## 2. Target Utente

**Target Principale:** Sviluppatore singolo o Power User che utilizza Claude Code per le proprie attività quotidiane di coding, analisi e documentazione, con più progetti attivi contemporaneamente e la necessità di riusare configurazioni tra loro.

**Esigenza dell'Utente:** Evitare la gestione manuale e frammentata di file JSON/Markdown sparsi tra `~/.claude/` e le cartelle `.claude/` di ogni progetto; avere un unico posto per decidere quali skill/agenti/MCP sono attivi dove, confrontare alternative, e capire quanto costa realmente ogni combinazione.

## 3. Architettura Applicativa e Stack

| Livello | Scelta |
|---|---|
| Backend | **Python + FastAPI** — serve sia le API/WebSocket sia il frontend (build statica React/Vite), raggiungibile via browser su `http://localhost:<porta>` |
| Frontend | **React (Vite) + TypeScript**, CSS Modules, **React Flow** per il canvas a nodi, **Zustand** per lo stato client, **TanStack Query** per lo stato server |
| Avvio/arresto | Script di avvio lanciato a comando dall'utente; pulsante "spegni" dentro l'app che termina il processo del server. Nessun servizio di sistema, nessun autostart |
| Storage indice/cache | **SQLite** utente (es. `~/.claude-control-plane/index.sqlite`): indice della libreria (cartelle/tag/bookmark), log di attivazione/disattivazione, cache telemetria — **mai** il contenuto dei pacchetti |
| Storage contenuto pacchetti (locale/progetto) | Cartella dedicata **dentro ogni progetto** (es. `.claude-control-plane/packages/<id>/`), non letta da Claude Code — tiene il progetto portabile e leggero; viaggia col progetto stesso |
| Storage contenuto pacchetti (globale) | Cartella utente dedicata (es. `~/.claude-control-plane/global-packages/<id>/`), dato che a livello globale non esiste una "cartella progetto" |

Il contenuto fisico dei pacchetti vive quindi accanto al progetto (o a livello utente per il globale); l'SQLite centrale serve solo a indicizzare/organizzare/confrontare, mai a duplicare i file.

### Fonti dati reali su cui si basa il Control Plane

Nessun servizio esterno è esposto nativamente da Claude Code: il control plane legge/scrive i file che Claude Code stesso usa. Reference completo in [docs/claude-code-reference/](docs/claude-code-reference/).

| Fonte | Contenuto | Uso |
|---|---|---|
| `~/.claude.json`, `~/.claude/settings.json`, `.mcp.json` di progetto | Config globale/progetto, `mcpServers`, `permissions`, `hooks` | Configuration Manager, MCP Hub |
| `.claude/skills/`, `.claude/agents/`, `.claude/commands/`, `~/.claude/` equivalenti | Skill, agenti, comandi (skill e comandi condividono lo stesso namespace di invocazione) | Library & Organization |
| `~/.claude/output-styles/`, `.claude/output-styles/` | Output style built-in e custom | Output Styles Manager |
| `~/.claude/projects/<project>/memory/MEMORY.md` + topic file | Auto memory: ciò che Claude impara sul progetto senza intervento utente | Auto Memory Viewer |
| `.claude/rules/*.md` con frontmatter `paths:` | Regole scoped per pattern di file, caricate on-demand | Rules Inspector |
| `~/.claude/sessions/<pid>.json` | Registro live processi `claude` attivi: `pid, sessionId, cwd, status busy/idle` | Live Activity Monitor — livello sessione |
| `~/.claude/projects/<url-encoded-cwd>/<session-uuid>.jsonl` | Transcript per sessione: `message.usage` per turno, eventi `tool_use`/`Task`, checkpoint | Token & Cost Dashboard, Live Activity Monitor — drill-down, Checkpoint Viewer |
| `~/.claude/jobs/<id>/`, mailbox JSON di agent team, worktree sotto `.claude/worktrees/` | Stato di agent view / agent team / dynamic workflow | Multi-Agent Monitor (fase successiva) |

**Nota sul parsing dei transcript `.jsonl`:** la documentazione ufficiale dichiara questo formato "interno, non garantito stabile tra versioni". Si è valutato di passare a OpenTelemetry (via nativo in Claude Code) come fonte più robusta, ma è stato deciso di **restare sul parsing diretto dei `.jsonl` per ora** — introdurre OTel richiederebbe tipicamente un collector esterno sempre attivo, in tensione con la scelta di non avere processi permanenti. Il modulo di parsing resta isolato dietro un'interfaccia sostituibile, con degrado controllato se il formato cambia (vedi [ARCHITECTURE.md](docs/planning/ARCHITECTURE.md)).

## 4. Requisiti e Funzionalità Principali

### Configuration Manager (scope globale)

- Editor visuale di `~/.claude.json`, `~/.claude/settings.json`, `~/.claude/CLAUDE.md`.
- A livello globale può esserci **una sola configurazione/pacchetto attivo alla volta** (per sua natura — è "l'ambiente di base" di ogni sessione Claude Code su questa macchina): attivarne uno nuovo disattiva il precedente.

### Local Package Manager (scope progetto)

- A differenza del globale, un progetto può avere **più pacchetti attivi contemporaneamente** (es. "frontend-web" + "secondbrain-obsidian" insieme) — skill e MCP sono per natura composabili.
- Scoperta progetti: **auto-scan** di `~/.claude/projects/` (progetti già toccati da Claude Code) **+ aggiunta manuale** di una cartella non ancora avviata.
- Creazione pacchetto: genera una cartella che segue le **convenzioni native riconosciute da Claude Code** (`.claude/skills/`, `.claude/agents/`, `.claude/commands/`, `.mcp.json`, `CLAUDE.md`, `.claude/settings.json`) — non un formato astratto da interpretare, ma file che la CLI userà nativamente non appena attivati.

### Meccanismo di attivazione/disattivazione

Attivare un pacchetto = copiare i suoi file dalla copia canonica (progetto o globale, vedi §3) nelle cartelle reali che Claude Code legge, in modalità **merge/append di default** (non sovrascrive ciò che c'è già) **con anteprima diff prima di scrivere**. Disattivare = rimuovere quegli stessi file dalle cartelle reali — con una verifica preventiva (manifest/hash di ciò che il Control Plane stesso ha scritto) per non cancellare per errore un file che l'utente ha creato o modificato manualmente nel frattempo.

Ogni attivazione/disattivazione viene registrata con timestamp in un **log** (non una semplice mappa "stato corrente"), per progetto e per pacchetto — necessario per il confronto storico nel Comparator (vedi sotto).

### MCP Server Hub

- Elenco, test, attivazione/disattivazione server MCP, sia globali (`~/.claude.json → mcpServers`) sia di progetto (`.mcp.json`).

### Library & Organization

Catalogo di tutte le risorse gestibili (skill, agenti, comandi, output style, pacchetti), organizzato con tre meccanismi distinti e non sovrapposti (da ricerca UI, vedi [docs/ricerca-ui-interattive-framework.md](docs/ricerca-ui-interattive-framework.md) §7):
- **Cartelle** — collocazione primaria e univoca (un elemento sta in una sola cartella; se sembra doverne stare in due, è la struttura da rivedere).
- **Tag** — filtro trasversale multi-select, piatto, indipendente dalla cartella corrente. Usato anche per marcare pacchetti "alternativi tra loro" (es. due candidati per lo slot "frontend"), utile al Comparator.
- **Bookmark/preferiti** — toggle binario, aggregato in una cartella virtuale "Preferiti", mai una terza tassonomia.

Le skill restano cataloghi/anteprima, **non editing di contenuto** — la scrittura sostanziale resta compito della CLI/editor esterno.

### Token & Cost Dashboard

Vista **read-only** (nessun enforcement/blocco — solo reportistica, per scelta esplicita):
- Costo e token aggregati per sessione, progetto, pacchetto, periodo.
- Fonte: parsing incrementale dei `.jsonl` + cumulativi già pronti in `~/.claude.json → projects.*`.

### Live Activity Monitor

Due livelli:
- **Sessione/progetto**: poll di `~/.claude/sessions/*.json`, push via WebSocket, stato busy/idle.
- **Drill-down skill/agente/tool**: tail dei `.jsonl` (sessione + subagent) per eventi `tool_use`/`Task`. Degrada in modo controllato se il parsing fallisce — mostra comunque il livello sessione.

### Multi-Agent Monitor *(fase successiva, non MVP)*

Estensione del Live Activity Monitor ai meccanismi di parallelismo di Claude Code non ancora coperti: **agent view** (`~/.claude/jobs/<id>/`, fino a 32 sessioni concorrenti), **agent team** (mailbox JSON, task list condivisa, sperimentale/opt-in), **dynamic workflow** (script orchestrati salvati in `.claude/workflows/`). Tutti tracciati localmente su filesystem, quindi compatibili con l'architettura filesystem-only — ma un pannello sostanzioso a sé, da progettare dopo che il monitor base è stabile.

### Visual Workflow Canvas & Recipe Bundler

- Canvas React Flow: nodi tipizzati (skill / agente / comando / MCP / regola / prompt), collegamenti concettuali.
- Salvataggio come pacchetto (schema §5), scritto nella copia canonica (progetto o globale).

### Workflow Comparator

Confronto tra pacchetti, su due assi:

- **Diff statico** — sempre disponibile, non richiede uso pregresso: composizione a confronto (skill, agenti, MCP, regole, prompt) tra due pacchetti qualsiasi.
- **Confronto storico** — richiede che i pacchetti siano stati effettivamente usati. Usa il log di attivazione/disattivazione (§ Meccanismo di attivazione) per attribuire le sessioni reali avvenute in ciascuna finestra temporale al pacchetto/combinazione corretta, poi aggrega costo/durata/token. Due modalità:
  - **Combinazione attiva nel tempo** (vista principale) — confronta un progetto in due periodi diversi in base a *quali pacchetti erano attivi insieme* (es. "con Obsidian" vs "senza Obsidian").
  - **Pacchetto isolato** (drill-down) — isola il contributo di un singolo pacchetto quando serve capire il suo effetto specifico, a prescindere da cos'altro era attivo.
- Il tag "alternativi" (§ Library) suggerisce automaticamente coppie di pacchetti candidati da confrontare quando ne esistono più di uno per lo stesso scopo.

*(Idea futura, non di default, non nell'MVP: slash command lanciabili da Claude Code che spediscono materiale — screenshot, report, snippet — al Control Plane per archiviazione, ad uso opt-in per arricchire il confronto con materiale qualitativo oltre alle metriche.)*

### Auto Memory Viewer *(da batch di estensione filesystem)*

Vista/audit di `~/.claude/projects/<project>/memory/MEMORY.md` e dei file tematici — cosa Claude ha imparato sul progetto, con storia di crescita nel tempo.

### Rules Inspector *(da batch di estensione filesystem)*

Vista delle regole in `.claude/rules/*.md` con pattern `paths:` e quando scattano.

### Checkpoint / Rewind Viewer *(da batch di estensione filesystem)*

Timeline dei checkpoint automatici per sessione (dato già presente nel transcript), con diff visuale e segnalazione esplicita di ciò che un checkpoint **non copre** (modifiche da comandi Bash, modifiche di subagent in background) — per non far affidamento erroneo sul rewind in quei casi.

### Sandboxing Config Editor *(da batch di estensione filesystem)*

Editor visuale per l'allowlist filesystem/rete enforced a livello OS dal sandboxing di Claude Code (distinto dalle regole di permesso `allow`/`deny`/`ask` già coperte dal Configuration Manager) — con un "simulatore" di cosa verrebbe bloccato.

### Output Styles Manager *(da batch di estensione filesystem)*

Catalogo/editor per gli output style (`~/.claude/output-styles/`, `.claude/output-styles/`, quelli bundlati nei pacchetti) — asse di configurazione distinto da CLAUDE.md/permessi/skill.

### Import/Export & Marketplace Hub

- **Export**: pacchetta un pacchetto (progetto o globale) in un formato portabile, sanitizzato (vedi §6), per riuso su un altro progetto o condivisione.
- **Import**: rileva prerequisiti mancanti (skill/MCP referenziati ma non presenti localmente) e guida la mappatura sulle risorse locali dell'utente.

## 5. Struttura del Pacchetto

```json
{
  "id": "obsidian-code-refactor",
  "name": "Refactoring basato su Note Obsidian",
  "version": "1.0.0",
  "scope": "project",
  "description": "Legge le specifiche dal Second Brain e applica il refactoring al codice.",
  "folder": "Frontend/Obsidian",
  "tags": ["obsidian", "refactor"],
  "mcp_dependencies": [
    { "id": "obsidian-mcp", "type": "obsidian", "required": true }
  ],
  "skills_required": [
    { "name": "clean-architecture-checker", "path": ".claude/skills/clean-architecture.md" }
  ],
  "agents_required": [],
  "commands_required": [],
  "instructions": "Analizza la nota specificata ed esegui il refactoring mantenendo il pattern descritto.",
  "canvas_layout": { "nodes": [], "edges": [] }
}
```

`scope: "global" | "project"` determina il modello di attivazione (singola vs composabile, §4). `folder`/`tags` alimentano la Library & Organization. Il campo `id` resta la chiave di correlazione per il Comparator e il log di attivazione.

## 6. Sicurezza e Considerazioni Locali

- **Esecuzione locale:** tutta l'app (backend + frontend servito) funziona su `localhost`, nessun accesso remoto.
- **Isolamento dei segreti:** chiavi API, percorsi assoluti, e la cache locale di telemetria/log di attivazione (dato d'uso personale) vengono rimossi automaticamente in fase di export — mai inclusi in un pacchetto condiviso.
- **Scrittura sicura sulle cartelle reali di Claude Code:** ogni scrittura è merge/append con anteprima diff; ogni rimozione verifica un manifest di ciò che il Control Plane stesso ha scritto, per non toccare modifiche manuali dell'utente. Attenzione al bug noto di Claude Code per cui `settings.local.json` può **sovrascrivere** (non fondere) i permessi globali — il Configuration Manager deve gestirlo esplicitamente, mai assumere un merge automatico.
- **Correlazione sessione↔pacchetto:** l'hook `SessionStart` che notifica il demone dell'avvio di una sessione (per popolare il log di attivazione con precisione) viene registrato come **entry diretta aggiunta all'array** `~/.claude/settings.json → hooks.SessionStart` (append sicuro, additivo rispetto alle entry di altri strumenti) — non come plugin Claude Code, per restare coerenti con il non-goal "non è un plugin".
- **ZDR e vincoli enterprise:** fuori scope per ora, essendo il perimetro filesystem-only single-user; da rivalutare se in futuro si aggiunge integrazione account.

## 7. Roadmap di Sviluppo

Vedi [docs/planning/IMPLEMENTATION_PLAN.md](docs/planning/IMPLEMENTATION_PLAN.md) per le fasi dettagliate con Definition of Done. In sintesi:

1. **Bootstrap** — scheletro FastAPI + frontend React/Vite servito, script di avvio/arresto.
2. **Core Backend** — Configuration Manager, MCP Hub, Library & Organization (lettura).
3. **UI Base + Token & Cost Dashboard**.
4. **Canvas & Live Activity Monitor** — composizione pacchetti, meccanismo di attivazione/disattivazione con manifest, monitor a due livelli.
5. **Workflow Comparator** — log di attivazione, diff statico + confronto storico a due modalità.
6. **Estensioni filesystem (batch)** — Auto Memory Viewer, Rules Inspector, Checkpoint Viewer, Sandboxing Editor, Output Styles Manager.
7. **Import/Export & Marketplace**.
8. **Multi-Agent Monitor** *(fase dedicata, dopo che il monitor base è stabile)*.
9. **Futuro, esplicitamente fuori scope attuale:** integrazione account claude.ai (Routines/Artifacts/Analytics/Remote Control), Claude Code embedded nell'app.
