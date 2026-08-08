---
status: accepted
---

# Live Activity Monitor integra il progetto mem0 reale, non una funzionalità equivalente costruita da zero

Per l'item TEST_NOTES.md "rielaborare Live Activity Monitor" l'utente vuole un report dei "pensieri e attività" di Claude visibile nativamente nel pannello, ispirato a [mem0](https://github.com/mem0ai/mem0) (memory layer per agenti LLM). In grilling session (2026-08-08) è stata scartata esplicitamente l'alternativa "costruire l'equivalente leggendo/estendendo il parsing dei transcript esistente" a favore di integrare il progetto mem0 stesso come dipendenza.

Deciso: mem0 viene importato/integrato come libreria reale, non reimplementato. L'adattamento dell'interfaccia (dove/come appare nel pannello) è esplicitamente rimandato dall'utente a quando si occuperà lui stesso di quella modifica — non fa parte del design da chiudere in questa sessione.

## Consequences

mem0 (pacchetto OSS `mem0ai`) tipicamente richiede una LLM per l'estrazione delle memorie e uno store per gli embedding — in modalità self-hosted entrambi sono configurabili su provider locali (l'ambiente ha già un server Ollama locale con `nomic-embed-text` per gli embedding, vedi CLAUDE.md utente globale), evitando così una dipendenza da un servizio cloud a pagamento e restando compatibile con il vincolo "filesystem-only, nessun processo permanente" del progetto — ma è una scelta implementativa (self-hosted vs piattaforma mem0 hosted con API key) non ancora chiusa, da risolvere quando si passa all'implementazione. Se si finisce sulla piattaforma hosted, serve gestione secret (API key) coerente con `docs/claude-code-reference` e le regole di sicurezza globali (mai hardcoded, sempre env var).
