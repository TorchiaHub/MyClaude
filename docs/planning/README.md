# Planning — Claude Code Control Plane

[← DESIGN.md](../../DESIGN.md) · [← docs/](../)

Indice dei documenti di pianificazione, pensati per essere eseguiti da Claude Code in autonomia:

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)** — architettura tecnica: componenti, stack, storage, contratto API, layout repo.
2. **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** — fasi di sviluppo, definition of done, rischi, principi di esecuzione (TDD, commit, review).
3. **[TASKS.md](./TASKS.md)** — task list granulare e sequenziale, organizzata per fase.

Contesto a monte:
- **[DESIGN.md](../../DESIGN.md)** — obiettivo, requisiti, decisioni prese in sessione di grilling.
- **[docs/claude-code-reference/](../claude-code-reference/)** — reference tecnico su Claude Code stesso (skill, agenti, comandi, hook, MCP, permessi, plugin, marketplace, e mappa completa della documentazione ufficiale). **Consultare prima di scrivere codice contro una qualunque superficie di Claude Code** — è verificato su fonti primarie, non da assumere da conoscenza pregressa.
- **[docs/](../)** — ricerche di supporto (controllo attività, UI/framework, strumenti community).

## Non-goal (da non perdere di vista durante l'implementazione)

- **Non è un IDE** — nessun editor di codice sorgente, nessuna esecuzione di sessioni Claude Code dentro l'app.
- **Non è un'app nativa** — web app pura (FastAPI + build statica React), niente Tauri/Electron.
- **Non è un plugin Claude Code** — nessun packaging `.claude-plugin/`, nessuna registrazione marketplace. Interagisce scrivendo/leggendo direttamente le cartelle reali.
- **Non è un processo permanente** — avvio manuale a comando, spegnimento da pulsante in UI.
- **Non si integra con l'account claude.ai** — perimetro filesystem-only; Routines/Artifacts/Analytics cloud/Remote Control restano fuori scope per ora.
