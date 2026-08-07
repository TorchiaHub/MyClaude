# Piano di implementazione — Claude Code Control Plane

[← README pianificazione](./README.md) · [Architettura](./ARCHITECTURE.md) · [Task list](./TASKS.md)

## Come eseguire questo piano in autonomia

Regole globali già attive per chi esegue (vedi `~/.claude/rules/ecc/common/`), da applicare senza ripeterle qui: TDD obbligatorio (RED → GREEN → REFACTOR, copertura 80%+, pattern AAA), file piccoli e focalizzati (200–400 righe tipiche), nessuna astrazione prematura, nessun commento se non sul *perché*, gestione esplicita degli errori, nessun segreto hardcoded, commit in formato `<type>: <description>` (conventional commits), code review (agente `code-reviewer` / skill `code-review`) dopo ogni fase prima di passare alla successiva.

**Prima di scrivere codice contro una qualunque superficie di Claude Code** (formato hook, schema plugin, sintassi permessi, formato transcript, ecc.), consultare [docs/claude-code-reference/](./../claude-code-reference/) — è il reference verificato su fonti primarie, da preferire a conoscenza pregressa che potrebbe essere datata.

**Ordine di esecuzione:** le fasi sono sequenziali. Dentro ogni fase, i task in [TASKS.md](./TASKS.md) sono ordinati per dipendenza. Ad ogni fase completata: eseguire i test, verificare la Definition of Done, poi commit.

## Fase 0 — Bootstrap

**Obiettivo:** repository funzionante, backend e frontend si avviano a comando.

- Init git, `.gitignore`, struttura cartelle come da [ARCHITECTURE.md](./ARCHITECTURE.md#layout-repository-proposto).
- Backend: scheletro FastAPI, ambiente Python (uv/poetry), pytest, endpoint `GET /health` + `POST /system/shutdown`.
- Frontend: scaffold Vite + React + TypeScript, build statica servita da FastAPI (nessuno shell nativo).
- Script di avvio (`./start.sh` o simile) che lancia il backend (che serve anche il frontend), apre il browser sulla porta locale.

**Definition of Done:** `pytest` verde; lo script di avvio apre l'app nel browser; il pulsante di spegnimento in UI termina il processo.

## Fase 1 — Core Backend

**Obiettivo:** `config_reader`, `mcp_manager`, `library_registry`, `project_discovery` funzionanti e testati, esposti via API.

- Per ciascun modulo: test prima (fixture `.claude.json`/`settings.json`/`.mcp.json`, **mai** i file reali dell'utente nei test), poi implementazione minima.
- `config_reader`: gestione esplicita del caso `settings.local.json` che sovrascrive (non fonde) i permessi globali — comportamento noto e documentato in [docs/claude-code-reference/hooks-mcp-permissions.md](../claude-code-reference/hooks-mcp-permissions.md).
- `library_registry`: scansione skill/agenti/comandi/output style, estrazione metadati, indice cartelle/tag/bookmark in SQLite.
- `project_discovery`: auto-scan `~/.claude/projects/` + registrazione manuale.

**Definition of Done:** test verdi, copertura ≥80%; via API si vedono config, libreria e progetti reali dell'utente.

## Fase 2 — UI Base + Token & Cost Dashboard

**Obiettivo:** interfaccia React per Configuration Manager, MCP Hub, Library & Organization (cartelle/tag/bookmark), Token & Cost Dashboard.

- Layout a pannelli, navigazione.
- `telemetry_reader`: parsing incrementale `.jsonl` + lettura cumulativi da `.claude.json` — test prima con fixture di transcript minimale.
- Dashboard: grafici trend costo/token per progetto/pacchetto/periodo (read-only).

**Definition of Done:** l'app mostra dati reali dell'utente (config, libreria, costi) aperti dal browser.

## Fase 3 — Canvas, Activation Engine & Live Activity Monitor

**Obiettivo:** comporre pacchetti sul canvas, attivarli/disattivarli sulle cartelle reali, monitorarli live.

- Canvas React Flow: nodi tipizzati (skill/agente/comando/MCP/regola/prompt), salvataggio come pacchetto (schema DESIGN.md §5) — `package_registry`, contenuto su filesystem (progetto o globale) + indice SQLite.
- `activation_engine`: merge/append con diff preview, scrittura `written_files` (manifest), rimozione verificata su manifest, regola "una recipe globale attiva" vs "N pacchetti locali attivi" — test prima, inclusi i casi limite (file modificato manualmente dall'utente dopo l'attivazione: la disattivazione **non** deve rimuoverlo).
- `activity_monitor` livello sessione: poll `~/.claude/sessions/*.json`, WS `/activity/live` — test prima con fixture directory sessioni.
- `activity_monitor` drill-down: tail `.jsonl` sessione + subagent — test prima, incluso il **degrado controllato** su formato non riconosciuto.

**Definition of Done:** si compone e attiva un pacchetto dal canvas, i file compaiono realmente in `.claude/`; disattivandolo spariscono (salvo modifiche manuali, preservate); il monitor mostra le sessioni reali entro 1–2s.

## Fase 4 — Workflow Comparator

**Obiettivo:** confronto statico e storico tra pacchetti.

- `hooks_installer`: aggiunge una entry all'array `hooks.SessionStart` (non un plugin) che notifica il backend; scrittura `session_started` — test prima su file di settings di fixture, mai quello reale.
- `comparator`: diff statico sui campi pacchetto; aggregazione storica incrociando `activation_log` + `session_started` + `telemetry_cache`, nelle due modalità (combinazione attiva nel tempo / pacchetto isolato) — test prima per ciascuna modalità.
- UI: selezione due pacchetti (o suggerimento automatico via tag "alternativi"), vista diff + metriche storiche affiancate.

**Definition of Done:** confrontando due pacchetti si vede sia la differenza di composizione sia, se esistono sessioni storiche correlate, il confronto di costo/durata/token per le due modalità.

## Fase 5 — Estensioni filesystem (batch)

**Obiettivo:** Auto Memory Viewer, Rules Inspector, Checkpoint Viewer, Sandboxing Editor, Output Styles Manager — tutte read-mostly, dati già sul filesystem.

- `memory_reader`, `rules_inspector`, `checkpoint_reader`, `sandbox_config`, output styles nel `library_registry` — ciascuno con test prima su fixture.
- Pannelli corrispondenti in UI.

**Definition of Done:** ciascun pannello mostra dati reali; il Checkpoint Viewer segnala esplicitamente cosa non è coperto da un checkpoint (modifiche Bash, subagent background).

## Fase 6 — Import/Export & Marketplace

**Obiettivo:** esportazione sanitizzata e importazione con risoluzione dipendenze.

- `sanitizer`: rimozione chiavi API/percorsi assoluti/cache locale (telemetria, log di attivazione) — test che asserisce esplicitamente l'assenza di questi campi nell'output.
- Import: rilevamento skill/MCP mancanti localmente, wizard di mapping.

**Definition of Done:** un pacchetto esportato e re-importato su una cartella di test pulita non contiene alcun dato locale sensibile, verificato via test automatico.

## Fase 7 — Multi-Agent Monitor *(dopo che le fasi precedenti sono stabili)*

**Obiettivo:** estendere il Live Activity Monitor a agent view / agent team / dynamic workflow.

- `multi_agent_monitor`: lettura `~/.claude/jobs/`, mailbox JSON di agent team, stato worktree — fase progettata a sé (schema dati, UI multi-sessione) quando si arriva qui, non pre-pianificata in dettaglio ora.

**Definition of Done:** da definire in una sessione di design dedicata a questa fase.

## Fuori scope (esplicitamente, non pianificare)

- Editor di codice sorgente / IDE.
- App nativa (Tauri/Electron), packaging come plugin Claude Code, processo permanente/autostart di sistema.
- Integrazione account claude.ai (OAuth, Routines, Artifacts, Analytics cloud, Remote Control) — perimetro filesystem-only per ora.
- Enforcement/blocco attivo sui budget token (solo reportistica).
- OpenTelemetry come fonte primaria (si resta su parsing `.jsonl`, per non introdurre un collector sempre attivo).
- **Idea futura, non di default:** slash command Claude Code che spediscono materiale (screenshot, report, snippet) al Control Plane per archiviazione — meccanica probabile: POST verso l'API locale, opt-in esplicito.

## Rischi trasversali da tenere presenti

| Rischio | Mitigazione |
|---|---|
| Formato dei transcript `.jsonl` non è un'API stabile | Isolare il parsing dietro un'interfaccia, degradare senza crash, testare con fixture versionate |
| Merge dei permessi non sempre additivo (`settings.local.json`) | Gestito esplicitamente in Fase 1 |
| Rimozione file su disattivazione può cancellare modifiche manuali dell'utente | Manifest/hash (`written_files`) verificato prima di ogni rimozione, mai assunto |
| Correlazione sessione↔pacchetto imprecisa senza hook `SessionStart` installato | Il comparator (Fase 4) non dipende da questa correlazione: `combination_mode_summary`/`isolated_mode_summary` incrociano direttamente `activation_log` (finestre attivate/disattivate) con i timestamp reali dei turni nel transcript, senza passare da `session_started`. L'hook e la tabella `session_started` restano disponibili (installabili da UI in Comparator, endpoint `/hooks/session-start/*`) come base per una correlazione più precisa in una fase futura, ma non sono nel percorso critico del confronto storico attuale |
| Scrittura diretta su cartelle reali di Claude Code (`.claude/skills/`, ecc.) | Sempre merge/append con anteprima diff, mai sovrascrittura silenziosa |
| ~~**[CRITICAL, deferred da Fase 1]** Nessuna protezione CORS/Origin sugli endpoint mutanti (`POST`/`DELETE /mcp/servers`, `POST /projects`, `POST /system/shutdown`, e ogni altro endpoint mutante aggiunto nelle fasi successive incl. `POST /packages/import`): una pagina web malevola aperta nello stesso browser può inviare richieste cross-origin "simple" (no preflight) che scrivono config MCP eseguibili da Claude Code o spengono il processo~~ — **Risolto**: `OriginGuardMiddleware` (`app/origin_guard.py`) applicato globalmente in `create_app()` rifiuta con 403 ogni richiesta `POST`/`PUT`/`PATCH`/`DELETE` il cui header `Origin` non corrisponde esattamente a scheme/hostname/porta della request stessa (derivati dall'header `Host`, non falsificabile lato JS in uno scenario cross-origin); le richieste **senza** header `Origin` passano invariate — scelta deliberata perché l'hook `SessionStart` chiama l'API via `curl` senza mai impostare `Origin`, e i browser moderni impostano sempre `Origin` sulle richieste cross-origin con metodo mutante (incl. il vettore "simple request" via `Content-Type: text/plain` senza preflight, e i submit di `<form>` nativi). `WS /activity/live` resta fuori scope di questo fix (nessun dato sensibile esposto, solo `session_id`/`cwd`/`status`) | — |
| ~~**[HIGH, deferred da Fase 1]** `json_store.write_json` non è atomica~~ — **Risolto**: scrive ora su file temporaneo nella stessa directory + `os.replace()` per sostituzione atomica, con cleanup del temp file su qualsiasi eccezione (incl. fallimento di `os.replace` stesso) | — |
| ~~**[HIGH, deferred da Fase 2]** SSRF via `POST /mcp/servers/{name}/test`~~ — **Risolto**: `check_reachability` ora risolve l'hostname e blocca esplicitamente indirizzi non instradabili pubblicamente (loopback, private, link-local incl. `169.254.169.254`, reserved, multicast) prima di qualunque richiesta HTTP in uscita | — |
| **[MEDIUM, deferred da Fase 2]** `telemetry_reader.summary._in_period` confronta i timestamp ISO-8601 come stringhe semplici: un turno con frazione di secondo (es. `...:00.500Z`) può risultare escluso da un filtro `since` sullo stesso secondo esatto (`.` precede `Z` lessicograficamente, invertendo l'ordine cronologico atteso in quel caso limite) | Parsare entrambi i lati con `datetime.fromisoformat` prima del confronto invece di affidarsi all'ordinamento lessicografico |
| ~~**[CRITICAL, deferred da Fase 3]** Path traversal via `package_id`/`node.name` (scrittura/cancellazione arbitraria) e `node.source_path` non validato (copia arbitraria di file, es. `~/.ssh`, `~/.claude.json`) in `package_registry`~~ — **Risolto**: `package_id` e i nomi nodo che finiscono in un path (skill/agent/command/rule) sono validati contro uno slug sicuro (`_validate_safe_identifier`, nessun `/`, nessun `..`); `source_path` non è più accettato dal client — l'API risolve i nodi skill/agent/command esclusivamente tramite `library_item_id` contro il catalogo reale (`library_registry.scan_library`), quindi un client non può più puntare a file arbitrari fuori dalla libreria catalogata; `project_path` per scope `project` deve ora essere un path assoluto | — |
| **[MEDIUM, deferred da Fase 3]** Possibile race condition nell'invariante "una sola recipe globale attiva": `activate_package` fa un `SELECT` sui pacchetti globali attivi correnti, poi disattiva e riscrive su un'unica connessione SQLite condivisa (`check_same_thread=False`) — due `POST /packages/{id}/activate` concorrenti su pacchetti globali diversi potrebbero, in teoria, non vedersi a vicenda tra la lettura e il commit finale, lasciando due pacchetti globali "attivi" nel manifest | Avvolgere il check-then-act in un'unica transazione, o inserire una riga di "prenotazione" prima del ciclo di scrittura file. Rischio basso in pratica per un'app desktop single-user con un solo utente che interagisce dalla UI, ma da chiudere se si introduce concorrenza reale (es. più tab/finestre) |
