# Ricerca: strumenti community per monitorare/gestire Claude Code

Elemento essenziale prima di procedere: **esiste già un progetto molto vicino all'obiettivo di questo DESIGN.md** — va valutato come riferimento architetturale (o come base da estendere) prima di scrivere codice da zero.

## Da valutare per primo: opcode (ex Claudia)

**[winfunc/opcode](https://github.com/winfunc/opcode)** — 15k+ stelle, GUI desktop per Claude Code costruita su **Tauri 2** (conferma empirica della scelta di stack indicata nell'altra ricerca). Struttura reale delle feature (verificata sul README):

- 🗂️ Project & Session Management
- 🤖 CC Agents
- 📊 Usage Analytics Dashboard
- 🔌 MCP Server Management
- ⏰ Timeline & Checkpoints
- 📝 CLAUDE.md Management

**Dettaglio "CC Agents" (la parte più vicina a "creazione/gestione", non solo monitoraggio):** è un editor per **singoli agenti individuali**, non un compositore di workflow — flusso `Create Agent → Configure (nome, icona, system prompt, modello, permessi read/write/network) → Execute`, con storico esecuzioni e run in background. **Verifica esplicita, in risposta al dubbio sollevato:** il README **non contiene** una sezione dedicata alle *skill* come entità configurabili separate dagli agenti, né un editor/composer visuale che concateni più agenti/skill/MCP/regole in un flusso — gli agenti restano entità autonome ed eseguibili singolarmente, non nodi di un grafo. Quindi la parte di gestione/creazione compositiva (skill + agenti + regole combinati in un workflow riusabile) — quella più rilevante per questo progetto — **non è coperta** da opcode: l'osservazione di una prevalenza di reportistica sull'uso è corretta.

Esiste anche un fork community, **[opcode-enhanced](https://github.com/skkoweio2/opcode-enhanced)**, che aggiunge gestione skill, template di prompt, notifiche multi-task e monitoraggio di "agent team" — più vicino a Skills Manager e Live Activity Monitor previsti in DESIGN.md, ma resta comunque privo di un canvas compositivo.

**Implicazione pratica:** opcode copre bene Project/Session Management, creazione di singoli agenti, MCP Hub e Usage Analytics (monitoraggio). La parte **non coperta**, che resta il cuore differenziante di questo progetto, è: gestione delle skill come entità di prima classe, **canvas visivo a nodi che compone skill + agenti + MCP + regole in un unico workflow**, formato di pacchetto/recipe esportabile, e il Workflow Comparator. Vale la pena valutare se partire da opcode come base per session/agent/MCP management e costruirci sopra la parte di canvas/recipe/comparator, invece di reimplementare anche quella base da zero.

## Strumenti focalizzati su token/costi (sovrapposti al Token & Cost Dashboard)

| Strumento | Tipo | Nota |
|---|---|---|
| [ccusage](https://ccusage.com/) | CLI locale | Legge i log locali (non solo Claude Code, anche Codex, Gemini CLI, ecc.) senza upload; forte per analisi storiche/trend settimanali. Utile come riferimento di parsing. |
| [Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) | Terminale | 8.5k★, previsioni di burn-rate e time-to-limit in tempo reale. |
| [claude-monitor (szaher)](https://github.com/szaher/claude-monitor) | Dashboard web | WebSocket live, tracking sessioni/token/costi/tool call, log file watching, import storico — architetturalmente il più simile al Live Activity Monitor + Token Dashboard di DESIGN.md. |
| [claude-usage (phuryn / flukelaster)](https://github.com/phuryn/claude-usage) | Dashboard web locale | Legge `~/.claude/projects/` **senza** contattare l'API Anthropic — stesso pattern di lettura dati già scelto in DESIGN.md §3. |
| [Sniffly](https://github.com/) *(cercare "Sniffly Claude Code dashboard")* | Dashboard web | Statistiche d'uso + analisi errori, condivisibile. |

## Lista curata utile al Marketplace Hub

- **[rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit)** — 135 agenti, 176+ plugin, 26 companion app, 52 voci di ecosistema catalogate: utile come sorgente per non duplicare skill/agenti già esistenti quando si popola l'Import/Export & Marketplace Hub del progetto.

*(Rimosse dalla ricerca: "happy" e "t3code" — companion app generiche di chat/coding, non riportano né aiutano a gestire l'attività di Claude Code in modo mirato; liste "awesome" duplicate — il vault Skills dell'utente usa già `hesreallyhim/awesome-claude-code` come fonte, e la lista sulla security è più pertinente alla ricerca sul controllo attività.)

## Fonti

- [GitHub - winfunc/opcode](https://github.com/winfunc/opcode)
- [opcode-enhanced](https://github.com/skkoweio2/opcode-enhanced)
- [ccusage.com](https://ccusage.com/)
- [Claude-Code-Usage-Monitor (Maciek-roboblog)](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor)
- [claude-monitor (szaher)](https://github.com/szaher/claude-monitor)
- [claude-usage (phuryn)](https://github.com/phuryn/claude-usage)
- [claude-usage (flukelaster)](https://github.com/flukelaster/claude-usage)
- [rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit)
