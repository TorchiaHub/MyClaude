# Ricerca: UI interattive per elementi eterogenei interconnessi — stili e stack

Elementi essenziali per progettare un'interfaccia intuitiva che gestisce entità diverse (workflow, skill, MCP, agenti) e le fa comunicare tra loro.

## 1. Canvas a nodi: React Flow è la scelta di default

Per il canvas visivo richiesto in DESIGN.md (§ Visual Workflow Canvas), **React Flow (xyflow)** è lo standard de facto: risolve già drag, zoom, pan, selezione, edge, handle, layout, persistenza e accessibilità — milioni di installazioni/settimana, manutenuto attivamente. **Rete.js** è l'alternativa da considerare solo se serve: supporto multi-framework (Vue/Svelte/Angular oltre React) o un motore integrato di dataflow/control-flow per eseguire davvero il grafo (non solo visualizzarlo). Per un frontend React come da DESIGN.md, React Flow richiede meno lavoro di integrazione.

## 2. Shell: web app pura, niente shell nativa (superato da decisione presa in sessione di grilling)

Il confronto Tauri vs Electron sotto è stato reso superfluo da una decisione successiva: il control plane è **una web app locale pura**, non un'app desktop nativa. Il backend FastAPI serve sia API/WebSocket sia il frontend React/Vite (build statica), raggiungibile via browser su `http://localhost:<porta>`. Avvio on-demand tramite script manuale + pulsante di spegnimento nell'app stessa — nessun processo permanente in background, nessun autostart di sistema. Questo elimina di netto tutti i problemi di packaging nativo (firma del codice, auto-update, installer per OS) che riguardano sia Tauri sia Electron: non essendoci un binario desktop da distribuire, quel livello di complessità non esiste per questo progetto. Confronto originale lasciato di seguito solo come nota storica:

| | Tauri 2 | Electron |
|---|---|---|
| Avvio | <0.5s | 1–2s |
| RAM idle | 20–100MB | 200–400MB |
| Dimensione bundle | fino a <1MB (minimo) | 150–200MB (Chromium incluso) |
| Backend nativo | Rust, webview di sistema | Chromium+Node bundlato |
| Ecosistema packaging | in crescita (+55% YoY repo) | maturo, più stabilito |

## 3. State management multi-pannello: Zustand invece di Redux

Per un'interfaccia con più pannelli indipendenti (canvas, dashboard token, monitor live, comparator), il consenso 2026 è: **Zustand** per lo stato client (2KB, nessun boilerplate/provider) + **TanStack Query** per lo stato server (dati letti dal demone Python, con caching/refetch integrato). Redux Toolkit resta preferibile solo se serve strumentazione/debugging enterprise strutturato, non è il caso di un'app locale single-user.

## 4. Comunicazione tra elementi eterogenei: pattern Event Bus / Pub-Sub

Workflow, skill, MCP e agenti sono entità di natura diversa che devono notificarsi cambi di stato (es. "skill X attivata" → il nodo canvas si aggiorna, il monitor live lo segnala) **senza conoscersi a vicenda**. Il pattern indicato è un Event Bus centrale: i moduli pubblicano eventi tipizzati, altri moduli si iscrivono a quelli di interesse, disaccoppiando i componenti da relazioni dirette parent-child. Per il control plane, questo si traduce in: un canale WebSocket/SSE lato demone che emette eventi tipizzati (`session.status_changed`, `tool.invoked`, `recipe.activated`, ecc.) e un event bus lato frontend (o direttamente lo store Zustand) che li instrada ai pannelli interessati.

## 5. Architettura a plugin per le entità gestite

Le entità gestite (skill, MCP server, recipe) vanno trattate come plugin di un core system: modulo con lifecycle esplicito (load → init → dispose), isolamento reciproco, estendibilità senza toccare il core. Coerente con come DESIGN.md già tratta Skills/MCP come risorse cataloga­bili indipendentemente — da mantenere anche nel Comparator e nel Live Monitor (ogni entità esposta con la stessa interfaccia minima: id, stato, metriche).

## 6. UX dashboard: coerenza riduce il carico cognitivo

Pattern di navigazione, etichette e stati di interazione coerenti tra i vari pannelli (canvas, dashboard, monitor, comparator) sono più importanti della ricchezza grafica del singolo pannello per la percezione di "intuitivo" — vale come principio guida quando si disegnano i quattro pannelli principali dell'app.

## 7. Organizzazione della libreria pacchetti: cartelle + tag + bookmark

Il gap lasciato aperto dalle sezioni precedenti è come organizzare la libreria di pacchetti (skill+agenti+MCP+regole) man mano che cresce a decine di elementi, senza far collassare l'interfaccia in un accumulo piatto o in un albero troppo rigido. La ricerca converge su un pattern preciso: **cartelle per la collocazione primaria univoca, tag come filtro trasversale piatto, bookmark come scorciatoia binaria** — tre meccanismi con ruoli distinti, non sovrapposti.

**Il riferimento diretto: Obsidian.** Il dibattito "cartelle vs tag" nella comunità Obsidian non produce un vincitore assoluto ma una divisione di responsabilità: le cartelle impongono una gerarchia rigida con **una sola collocazione per nota**, i tag sono piatti, senza relazione parent-child, e permettono a una nota di comparire in più insiemi contemporaneamente. La sintesi più utile (Eleanor Konik) è pratica, non ideologica: le cartelle restano superiori come "home" primaria perché compatibili nativamente con filesystem/ricerca/UI a albero, mentre "usare i tag per tutto rende i tag meno utili" — mescolare tassonomia e stati/flag nei tag crea rumore. La regola operativa che ne deriva è l'**unicità di collocazione**: se un elemento sembra poter stare in due cartelle, è la struttura delle cartelle che va consolidata, non l'elemento che va duplicato. Il recente plugin Bases di Obsidian conferma questa direzione: costruisce viste "database" (tabella/card/lista) sopra cartelle e proprietà (tra cui `tags` come lista), cioè usa le cartelle come ambito e i tag/proprietà come colonne filtrabili — esattamente la dualità richiesta qui.

**Conferma dai tool creativi/dev.** Figma organizza le component library con una gerarchia a due livelli (pagina = categoria, sezione = sotto-categoria, 1-5 componenti per sezione) più naming a slash (`Categoria/Variante`) per il resto — gerarchia fissa per la collocazione, non tag liberi. Il VS Code Extensions Marketplace fa l'opposto per la scoperta: **categorie fisse** (Linters, Themes, Debuggers...) combinate con **tag liberi** filtrabili via prefissi `category:` e `tag:` nella barra di ricerca — un pattern di ricerca faceted sovrapposto a una tassonomia base. Notion, nelle gallery view, separa esplicitamente la proprietà multi-select ("tag che si sovrappongono") dai filtri di vista e da un eventuale flag "Featured" — tre meccanismi indipendenti nello stesso database.

**Faceted vs gerarchia: quando usare cosa.** La letteratura di information architecture è netta: la classificazione gerarchica forza un solo percorso di accesso e un ordine fisso degli attributi, mentre la classificazione a faccette permette multidimensionalità e scala bene quando le categorie crescono nel tempo senza un piano prestabilito — esattamente il caso di una libreria che passa da pochi a decine di pacchetti eterogenei. Per un utente singolo (non un team che deve concordare una tassonomia condivisa), il costo di mantenere le faccette (tag) è basso perché non serve consenso, mentre la gerarchia (cartelle) resta comunque preziosa come "indirizzo" stabile e prevedibile per tornare a un elemento noto — le due cose non competono, rispondono a bisogni diversi (browsing esplorativo vs richiamo diretto).

**Il bookmark non è una terza tassonomia.** Il pattern UI "favorites/star" è per definizione binario e va tenuto fuori dalla logica di categorizzazione: la guida di riferimento è esplicita — *"non usare i preferiti per selezionare più categorie, per quello ci sono tag o categorie"*. Il suo ruolo è solo accesso rapido a un sottoinsieme piccolo e mutevole ("i pacchetti che uso questa settimana"), non un modo alternativo di classificare.

### Raccomandazione concreta per il control plane

- **Sidebar sinistra = albero cartelle**, unica gerarchia di collocazione. Ogni pacchetto vive in *esattamente una* cartella/sottocartella (es. `frontend-web`, `devops/ci`, `secondbrain-obsidian`). Nessuna collocazione multipla: se un pacchetto sembra appartenere a due cartelle, è un segnale che la cartella va scissa o il pacchetto va scomposto — stessa regola di consolidamento vista in Obsidian.
- **Riga filtri sopra la griglia principale = tag multi-select**, piatti, liberi, cross-cutting (`ui`, `python`, `wip`, `experimental`). Selezionabili in AND/OR come chip rimovibili (pattern VS Code Marketplace / Notion multi-select), indipendenti dalla cartella corrente: navigare in una cartella e poi affinare con tag è il flusso primario di scoperta.
- **Bookmark/star** come singola icona toggle sulla card del pacchetto (stato binario, non annidabile), con una voce fissa **"Preferiti"** in cima all'albero cartelle — una cartella *virtuale*, non una posizione reale, che aggrega per stella indipendentemente da dove il pacchetto vive davvero. Non introdurre un secondo livello di "preferiti dentro preferiti": è lo stesso errore che il pattern avverte di evitare.
- **Ricerca globale unificata** in stile VS Code (`tag:python cartella:devops testo libero`) sopra la griglia, per bypassare l'albero quando l'utente sa già cosa cerca — la faceted search come scorciatoia rispetto alla gerarchia, non in sostituzione.
- **Stato in Zustand**: uno store `libraryStore` separato dal grafo React Flow del canvas — la libreria è un pannello di catalogo (grid/list), il canvas è lo spazio di composizione. Forma minima: albero cartelle (struttura ricorsiva id/nome/parentId), mappa `packageId → Set<tag>`, `Set<packageId>` per i preferiti, più lo stato di filtro corrente (cartella attiva, tag selezionati, query testuale) — tre strutture dati indipendenti che si combinano solo in fase di rendering/filtro, mai fuse in un unico campo. Trascinare una card dalla griglia sul canvas React Flow istanzia il nodo corrispondente, mantenendo library e canvas disaccoppiati (coerente con l'event bus di §4: `package.dragged_to_canvas` come evento, non chiamata diretta).

## Fonti

- [React Flow — Node-Based UIs in React](https://reactflow.dev/)
- [awesome-node-based-uis (xyflow)](https://github.com/xyflow/awesome-node-based-uis)
- [Rete.js — JavaScript framework for visual programming](https://retejs.org/)
- [Tauri vs Electron 2026 — DigitalApplied](https://www.digitalapplied.com/blog/desktop-apps-web-stack-tauri-electron-deno-wails-2026)
- [Tauri v2 vs Electron 2026: The Honest Comparison](https://www.buildmvpfast.com/blog/tauri-v2-vs-electron-desktop-apps-2026)
- [Redux vs Zustand vs Context API in 2026](https://medium.com/@sparklewebhelp/redux-vs-zustand-vs-context-api-in-2026-7f90a2dc3439)
- [React State Management Comparison 2026 — Woyable](https://woyable.com/en/posts/react-state-management-comparison)
- [Frontend System Design: Event Handling and Pub/Sub Patterns](https://dev.to/zeeshanali0704/frontend-system-design-event-handling-and-pubsub-patterns-120i)
- [Plugin Architecture Design Pattern — A Beginner's Guide to Modularity](https://www.devleader.ca/2023/09/07/plugin-architecture-design-pattern-a-beginners-guide-to-modularity)
- [Dashboard Design Principles: The Definitive Guide 2026 — UXPin](https://www.uxpin.com/studio/blog/dashboard-design-principles/)
- [Yet Another Hot Take on "Folders vs Tags" — Eleanor Konik](https://www.eleanorkonik.com/p/yet-another-hot-take-on-folders-versus-tags)
- [How to Structure Notes — Categories, Tags, and Folders (Obsidian Forum)](https://forum.obsidian.md/t/how-to-structure-notes-categories-tags-and-folders/103125)
- [Obsidian Bases: The Complete Guide to Database Views (2026)](https://got.md/obsidian-bases/)
- [Facets, But Which Ones? — Daniel Tunkelang](https://dtunkelang.medium.com/facets-but-which-ones-6589416ed4db)
- [Faceted classification: management and use (arXiv)](https://arxiv.org/pdf/1705.07047)
- [Name and organize components — Figma Learn](https://help.figma.com/hc/en-us/articles/360038663994-Name-and-organize-components)
- [VS Code Extension Marketplace — categorie, tag, filtri](https://code.visualstudio.com/docs/configure/extensions/extension-marketplace)
- [Notion Multi-select Property: Tag Rows with Multiple Labels](https://www.sparxno.com/blog/notion-multi-select)
- [Favorites design pattern — UI-Patterns.com](https://ui-patterns.com/patterns/favorites)
- [Filter UI design: Sidebar vs top bar vs inline patterns — Setproduct](https://www.setproduct.com/blog/filter-ui-design)
