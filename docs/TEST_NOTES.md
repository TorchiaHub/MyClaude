# Note di test — annotazioni grezze

Log delle annotazioni raccolte durante lo smoke test manuale. Riportate come dette, senza elaborazione.

---

- Promemoria da aggiungere come avviso in UI dopo ogni scrittura effettiva in una tab: indicare il comando/metodo corretto per rendere effettivo il cambiamento nella sessione Claude Code corrente, specifico per tipo di modifica (reload sessione, `/reload-plugins`, skill/MCP hanno rilevamento live proprio, ecc.).

- MCP: aggiungi collegamento al percorso cartelle e rispettivi file, visualizzare gli MCP sorgenti + tasto "claude code" per un avvio rapido.

- Da cambiare la gestione delle cartelle e dei percorsi di progetti (il pulsante in alto a destra).

- Canvas Pacchetti precarica l'ultimo pacchetto canvas a cui si stava lavorando.

- Aggiungere la funzionalità di lettura e visualizzazione di agent/prompt/skills ed altro su canvas.

- Aggiungere la ricerca per ogni singolo elemento (da integrare anche per il tasto di ricerca del progetto tra globale e locale).

- Aggiungere l'import automatico dei file/cartelle/progetti all'interno dei progetti e il CLAUDE.md ed anche hooks e tutte le tipologie di file importabili su Claude Code per fargli svolgere meglio il suo lavoro.

- ID pacchetto: rendere la generazione del numero automatica e riportarla ogni volta che si carica un canvas workflow.

- Rielaborare la sezione Live Activity Monitor (cercando di monitorare più dati, oppure cambiando la sua posizione da menù/tab a dato aggiuntivo magari su Configuration Manager).

- Aggiungere la lettura e la visualizzazione delle cartelle (come le modifiche suggerite prima) su Comparator.

- Su Import/Export aggiungere file .md ed altri tipi di file trattati dal progetto.

- Creare una gerarchia ed un ordine logico di visualizzazione del canvas di Claude Globale, per non renderlo solo verticale.

- Da valutare in futuro (non ancora deciso, solo da tenere in lista): aggiungere il progetto NVIDIA SkillSpector.

- Da valutare in futuro (non ancora deciso, solo da tenere in lista): aggiungere una connessione a un marketplace di skill/agenti/MCP/hook.

- **Correzione (grilling session 2026-08-08):** il riferimento a mem0 **non** è un pacchetto da importare — l'utente vuole una funzionalità nativa nel Live Activity Monitor, ispirata a mem0, che mostri un "report dei pensieri e delle attività di Claude" (non solo tool_use/Task come oggi). Dettagli tecnici (uso della libreria mem0 vs building from scratch sui transcript, scope live-vs-storico) ancora da chiarire — vedi round 3 della grilling session per il seguito.
