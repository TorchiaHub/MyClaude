---
status: accepted
---

# Default UI: editing pieno dove ha senso, non più "read-mostly per prudenza"

Fase 5 aveva scelto deliberatamente un design "tutte read-mostly" per Auto Memory/Rules/Checkpoint/Sandboxing/Output Styles (nessun endpoint di scrittura), nonostante DESIGN.md §4 originale descrivesse alcuni di questi come editabili ("Sì (form)"). In grilling session (2026-08-08), l'utente ha respinto esplicitamente questo default cauto: vuole controllo ed edit completo, incluso poter leggere/editare il CLAUDE.md globale (oggi assente da Configuration Manager, che espone solo `claude.json`/`settings.json`).

Deciso: il default per le prossime modifiche UI è editing pieno ovunque l'operazione abbia un significato coerente (es. Sandboxing Editor, Output Styles Manager, Auto Memory, Rules Inspector, CLAUDE.md globale in Configuration Manager) — non più read-only per scelta di scope. Fa eccezione ciò per cui "editing" non ha un significato ben definito (es. un Checkpoint storico nel transcript non è un dato modificabile in sé — resta un'azione di rewind delegata alla CLI, come da design originale).

Questa decisione riguarda **solo la superficie di editing esposta**, non la sua validazione: i controlli server-side esistenti (validazione di `library_item_id` invece di path client-side, guard di root-escape in `home_browser`) restano invariati e si applicano allo stesso modo a ogni nuovo endpoint di scrittura aggiunto sotto questa policy — i due assi (chi può scrivere cosa / come viene validato l'input) sono indipendenti.

## Consequences

Ogni pannello Fase 5 che diventa editabile richiede un endpoint `PUT`/`PATCH` dedicato con lo stesso trattamento anteprima-diff/manifest già usato da `activation_engine` dove la scrittura tocca cartelle reali di Claude Code.

**Perimetro finale (round successivi della stessa grilling session, 2026-08-08):**
- Configuration Manager diventa l'editor di **tutti** i file di configurazione Claude Code non già di proprietà di un altro pannello: `CLAUDE.md` (globale e di progetto), le altre chiavi di `~/.claude.json`/`settings.json` oltre ai permessi, **incluso `settings.local.json`** — nessuna eccezione read-only, nemmeno per il comportamento non-merge noto (mitigato con un avviso persistente in UI quando si edita quel file specifico, non con un blocco di scrittura). `.mcp.json` resta di proprietà di MCP Hub, che lo edita già per intero — Configuration Manager non lo duplica.
- Sandboxing Editor e Output Styles Manager: editabili senza riserve.
- Rules Inspector: editing diretto del contenuto.
- Auto Memory Viewer: editabile, con avviso esplicito in UI che Claude Code può sovrascrivere la modifica alla sessione successiva.
- Checkpoint Viewer resta l'unica eccezione strutturale (non un'eccezione di prudenza): un checkpoint storico non è un dato modificabile, l'azione resta il rewind delegato alla CLI.
