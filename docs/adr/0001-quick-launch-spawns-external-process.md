---
status: accepted
---

# Il backend può spawnare processi OS (reveal-in-file-manager, quick-launch terminale)

Il DESIGN.md originale (§1) elenca come non-goal esplicito "nessuna esecuzione di sessioni Claude Code dentro l'app" — letto finora come "il backend non spawna mai processi arbitrari". In grilling session (2026-08-08) l'utente ha chiesto due funzionalità che richiedono comunque di far spawnare al backend un processo OS: (1) un tasto "apri nel file manager" su un percorso reale (MCP Hub, Comparator), riusabile — non solo copia del path in appunti; (2) un tasto "avvia Claude Code" per un avvio rapido da MCP Hub, implementazione rimandata a una fase successiva.

Deciso: il non-goal resta "nessuna sessione Claude Code eseguita/embedded dentro l'app" (l'app non diventa un terminale, non cattura I/O di una sessione `claude`), ma non si estende più a "il backend non spawna mai un processo OS". Entrambe le funzionalità sopra sono ammesse. Resta da definire, quando si implementa (2), se lancia un terminale con `claude` pre-digitato o solo apre una shell nella cartella — decisione rimandata all'implementazione.

## Consequences

Ogni endpoint che spawna un processo (`xdg-open`/`open`/`explorer`, o un lancio di terminale) prende lo stesso trattamento di sicurezza già usato per `home_browser`: path risolto e validato server-side prima dello spawn, mai una stringa di comando costruita da input diretto del client.
