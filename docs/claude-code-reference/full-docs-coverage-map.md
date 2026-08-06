# Claude Code — Mappa completa della documentazione ufficiale (full-docs-coverage-map)

> Scansione sistematica dell'intero indice di `code.claude.com/docs` (176 pagine, agosto 2026), con focus su tutto ciò che **non** è coperto dai tre documenti di reference già scritti. Per il Control Plane: elenco esaustivo + valutazione esplicita "va gestito/visualizzato?" per ogni area nuova rilevante.

---

## Fonti

**Indice canonico usato per la scansione:** `https://code.claude.com/docs/llms.txt` — indice ufficiale machine-readable con tutte le 176 pagine, titolo, URL e descrizione one-line. Verificato che `code.claude.com/docs` è l'host canonico (conferma indipendente, coerente con gli altri tre documenti: `docs.claude.com/en/docs/claude-code/*` fa 301 redirect lì).

**Pagine fetchate per intero durante questa ricerca** (oltre alla scansione dell'indice): `checkpointing.md`, `costs.md`, `output-styles.md`, `memory.md`, `context-window.md`, `vs-code.md`, `jetbrains.md`, `headless.md`, `model-config.md`, `interactive-mode.md`, `keybindings.md`, `github-actions.md`, `admin-setup.md`, `monitoring-usage.md`, `agent-sdk/overview.md`, `features-overview.md`, `agent-view.md`, `agent-teams.md`, `workflows.md`, `routines.md`, `sessions.md`, `sandboxing.md`, `claude-code-on-the-web.md`, `zero-data-retention.md`, `remote-control.md`, `channels.md`, `worktrees.md`, `artifacts.md`, `code-review.md`, `chrome.md`. Le restanti ~145 pagine sono riportate con sintesi da 2-4 righe basate sulla descrizione ufficiale dell'indice (`llms.txt`) più, dove pertinente, cross-reference dal contenuto delle pagine fetchate che le citano.

**Documenti di reference già prodotti (da NON ripetere qui, solo referenziati)**:
- `/home/matt/Documents/MY_CLaude/docs/claude-code-reference/skills-agents-commands.md` — Skills, Subagent, Slash command
- `/home/matt/Documents/MY_CLaude/docs/claude-code-reference/hooks-mcp-permissions.md` — Hooks, MCP, Permessi/Settings
- `/home/matt/Documents/MY_CLaude/docs/claude-code-reference/plugins-marketplace-config.md` — Plugin, Marketplace, mappa config

---

## Come leggere questo documento

- **§1** è l'elenco esaustivo delle 176 pagine, organizzato per area tematica, 2-4 righe ciascuna, con nota `[GIÀ COPERTO]` dove il contenuto è già nei tre documenti precedenti.
- **§2** approfondisce le aree **nuove** più rilevanti per un Control Plane visivo, con outcome esplicito **Sì / No / Forse** su "il Control Plane dovrebbe gestirlo/visualizzarlo?".
- **§3** è una sintesi finale con la lista delle nuove domande di design aperte.

---

## 1. Indice completo per area (176 pagine)

### 1.1 Onboarding, concetti base, piattaforme

| Pagina | Sintesi |
|---|---|
| `overview.md` | Homepage della documentazione. Elenca le 6 superfici (terminale, VS Code, Desktop, Web, JetBrains, mobile) e rimanda a tutte le feature principali. Utile come mappa di partenza ma zero dettaglio tecnico proprio. |
| `quickstart.md` | Primo task guidato end-to-end: installazione, primo prompt, prima modifica, primo commit. |
| `setup.md` | Setup avanzato: requisiti di sistema, installazione per piattaforma (incl. `apt`/`dnf`/`apk` su Linux), gestione versioni, disinstallazione. |
| `troubleshoot-install.md` | Errori di installazione/login mappati a fix specifici (PATH, permessi, rete, auth). |
| `how-claude-code-works.md` | Spiega il loop agentic, i tool nativi, come Claude interagisce col progetto — base concettuale per §"context window" e tool-reference. |
| `platforms.md` | Tabella comparativa: dove eseguire Claude Code (CLI/Desktop/VS Code/JetBrains/web/mobile) e cosa collegarci (Chrome, Slack, CI/CD). |
| `feature-availability.md` | Matrice feature × piano (Pro/Max/Team/Enterprise) × provider (Console, Bedrock, Claude Platform on AWS, Google Cloud's Agent Platform, Microsoft Foundry). Cruciale per capire cosa è disponibile dove. |
| `glossary.md` | Glossario terminologico ufficiale: agentic loop, compaction, CLAUDE.md, hooks, subagents, MCP, ecc. |
| `common-workflows.md` | Guide passo-passo per task ricorrenti (esplorare codebase, fix bug, refactoring, testing). |
| `best-practices.md` | Tips per ottenere il massimo da Claude Code, config ambiente, scaling su sessioni parallele. |
| `prompt-library.md` | Libreria di prompt copiabili, taggati per task/ruolo. |
| `champion-kit.md` | Playbook per chi promuove Claude Code internamente in azienda (cosa condividere, come rispondere a domande). |
| `communications-kit.md` | Materiali per annunci/rollout interno: messaggi di lancio, FAQ, campagne drip. |
| `changelog.md` | Release notes per versione. |
| `whats-new/index.md` + `whats-new/2026-w13.md`…`2026-w29.md` (17 pagine settimanali) | Digest settimanale delle feature notevoli, con snippet e demo. Copre l'intera storia recente: auto mode, computer use, PR auto-fix, `/ultrareview`, Sonnet 5 come default, Claude Desktop su Linux, ecc. |
| `errors.md` | Reference di tutti i messaggi di errore runtime, causa e fix. |
| `troubleshooting.md` | Fix per CPU/memoria alta, hang, thrashing di auto-compact, problemi di ricerca. |
| `devcontainer.md` | Esecuzione in dev container per ambienti isolati e consistenti nel team. |

### 1.2 IDE, editor e superfici desktop/mobile

| Pagina | Sintesi | Copertura |
|---|---|---|
| `vs-code.md` | Estensione VS Code: pannello grafico nativo, diff inline, @-mention, plan review, cronologia conversazioni, gestione plugin via `/plugins`, server MCP `ide` interno. Vedi §2.4 per deep-dive. | **NUOVO — approfondito in §2.4** |
| `jetbrains.md` | Plugin per IntelliJ/PyCharm/WebStorm/ecc: lancia `claude` nel terminale integrato, diff viewer nativo, `/ide` per collegare da terminale esterno. Vedi §2.4. | **NUOVO — approfondito in §2.4** |
| `desktop.md` | App standalone: sessioni parallele con isolamento Git, layout drag-and-drop, terminale+editor integrati, side chat, computer use, Dispatch da telefono, review diff visuale, app preview, monitoraggio PR, connector, config enterprise. | **NUOVO — non approfondito oltre, vedi §2.9** |
| `desktop-quickstart.md` | Setup rapido app desktop. | Minore |
| `desktop-scheduled-tasks.md` | Task ricorrenti eseguiti **localmente** sulla macchina (non cloud) dall'app Desktop. | **NUOVO — vedi §2.7 Routines/Scheduling** |
| `desktop-ios-simulator.md` | L'app Desktop apre l'iOS Simulator in un pannello quando Claude builda/lancia un'app, un simulatore per sessione. | Minore, verticale specifico |
| `desktop-linux.md` | App Desktop in beta su Ubuntu/Debian. | Minore |
| `desktop-wsl.md` | Sessioni Code eseguite dentro una distro WSL2 da Desktop su Windows. | Minore, ma rilevante per enterprise (vedi admin-setup) |
| `mobile.md` | App Claude per iOS/Android: avvia, monitora, steer task da telefono. | **NUOVO — vedi §2.7** |
| `deep-links.md` | Link `claude-cli://` per aprire una sessione terminale da URL (runbook, alert, dashboard). | **NUOVO, minore** |
| `fullscreen.md` | Modalità di rendering fullscreen flicker-free con supporto mouse, per conversazioni lunghe. | **NUOVO, minore — UI terminale** |
| `terminal-config.md` | Fix per Shift+Enter, bell di notifica, tmux, tema colori, vim mode. | **NUOVO, minore** |
| `accessibility.md` | Setup screen reader (VoiceOver/NVDA), lenti d'ingrandimento, motion ridotto, temi per daltonici. | **NUOVO — vedi §2.10** |
| `voice-dictation.md` | Dettatura vocale hold-to-record/tap-to-record nella CLI. | **NUOVO, minore** |

### 1.3 CLI, esecuzione headless, tool

| Pagina | Sintesi | Copertura |
|---|---|---|
| `cli-reference.md` | Reference completa di comandi e flag CLI. | **NUOVO (parzialmente citato negli altri doc, ma non trattato come pagina a sé) — vedi §2.5** |
| `headless.md` | Esecuzione programmatica via `claude -p`: bare mode, output JSON/stream-json, gestione retry, eventi `system/init`, streaming subagent, auto-approve tool. Base per SDK e CI/CD. | **NUOVO — approfondito in §2.5** |
| `env-vars.md` | Reference delle variabili d'ambiente che controllano il comportamento. | **NUOVO — trasversale, vedi §2.5** |
| `tools-reference.md` | Reference di tutti i tool nativi (permessi richiesti, comportamento per-tool). | Parzialmente già citato negli altri doc (MCP tool naming); qui è la fonte primaria completa |
| `interactive-mode.md` | Reference completa di scorciatoie da tastiera e input mode. | **NUOVO — approfondito in §2.6** |
| `keybindings.md` | File `~/.claude/keybindings.json` per rimappare scorciatoie, context, chord binding. | **NUOVO — approfondito in §2.6** |
| `statusline.md` | Status bar custom per context window, costi, stato git. | **NUOVO, minore — già menzionato indirettamente (statusLine in settings) ma non come feature UI** |

### 1.4 Sessioni, memoria, contesto

| Pagina | Sintesi | Copertura |
|---|---|---|
| `sessions.md` | Gestione sessioni: naming, resume/continue/branch, `--from-pr`, picker, export transcript, storage location. | **NUOVO — approfondito in §2.2** |
| `checkpointing.md` | Rewind automatico di codice+conversazione (`/rewind`), summarize, limiti (bash non tracciato, subagent non tracciato, symlink skippati). | **NUOVO — approfondito in §2.1** |
| `memory.md` | CLAUDE.md avanzato: gerarchia file, import `@path`, `.claude/rules/` con `paths:` frontmatter, auto memory (MEMORY.md), troubleshooting. | **NUOVO — approfondito in §2.3 (auto memory è la parte davvero nuova)** |
| `context-window.md` | Simulazione interattiva di cosa riempie il context window, costo di ogni file read, quando scattano rule/hook, cosa sopravvive a `/compact`. | **NUOVO — approfondito in §2.3** |
| `prompt-caching.md` | Come funziona il prompt caching in Claude Code: perché un cambio modello innesca un turno lento, costo di `/compact`, cache hit rate. | **NUOVO, tecnico — vedi §2.3** |
| `claude-directory.md` | Tour di `.claude/` e `~/.claude/`: dove vivono CLAUDE.md, settings, hooks, skills, comandi, subagent, workflow, rules, auto memory. | Sostanzialmente una mappa di navigazione — incrocia tutti gli altri doc, minimo contenuto nuovo proprio |
| `large-codebases.md` | Config per monorepo/codebase grandi: CLAUDE.md annidati, worktree sparse, code intelligence, skill per-package. | **NUOVO, rilevante enterprise** |

### 1.5 Modello e ragionamento

| Pagina | Sintesi | Copertura |
|---|---|---|
| `model-config.md` | Alias modello (`opus`,`sonnet`,`fable`,`opusplan`,`[1m]`), effort level, extended thinking, adaptive reasoning vs fixed budget, fallback chain, restrizioni org. | **NUOVO — approfondito in §2.1 (extended thinking/reasoning)** |
| `advisor.md` | Tool "advisor": abbina il modello principale a un modello più forte che Claude consulta in momenti chiave del task. | **NUOVO — approfondito in §2.1** |
| `fast-mode.md` | Risposte Opus più veloci tramite toggle "fast mode". | **NUOVO, minore** |

### 1.6 Multi-agente, parallelismo, orchestrazione

| Pagina | Sintesi | Copertura |
|---|---|---|
| `agents.md` | Pagina di confronto: subagent vs agent view vs agent team vs dynamic workflow — quale usare quando. | **NUOVO — utile come indice, contenuto assorbito in §2.2** |
| `agent-view.md` | `claude agents`: dispatch/monitor/gestione multi-sessione da un'unica schermata, supervisor process, worktree isolation automatica, filtri, PR tracking. | **NUOVO — approfondito in §2.2** |
| `agent-teams.md` | Team di sessioni Claude Code indipendenti che comunicano tra loro (mailbox, task list condivisa), lead + teammate, split-pane con tmux/iTerm2. Sperimentale, opt-in via env var. | **NUOVO — approfondito in §2.2** |
| `workflows.md` (dynamic workflows) | Script JS scritto da Claude che orchestra subagent a scala (fino a 1000 agent/run), eseguito da un runtime separato, resumable, salvabile come comando `/nome`. `/deep-research` bundled. | **NUOVO — approfondito in §2.2, alta priorità** |
| `worktrees.md` | Isolamento file via git worktree: `--worktree`, `EnterWorktree`/`ExitWorktree` tool, `.worktreeinclude`, cleanup automatico, hook per VCS non-git. | **NUOVO — approfondito in §2.2** |

### 1.7 Automazione programmata e trigger esterni

| Pagina | Sintesi | Copertura |
|---|---|---|
| `routines.md` | Agenti cloud schedulati gestiti da Anthropic: trigger schedule/API/GitHub event, girano anche a laptop chiuso, `/schedule` in CLI. | **NUOVO — approfondito in §2.7, alta priorità** |
| `scheduled-tasks.md` | `/loop` e cron tool **dentro una sessione CLI aperta** — locale, non persistente oltre la sessione. | **NUOVO — approfondito in §2.7** |
| `desktop-scheduled-tasks.md` | Task schedulati **locali** (girano sulla macchina, non cloud) dall'app Desktop. | **NUOVO — vedi §2.7** |
| `goal.md` | `/goal`: condizione di completamento esplicita, Claude continua a lavorare su più turni finché non è soddisfatta. | **NUOVO, minore ma interessante per automazione** |
| `github-actions.md` | GitHub Action ufficiale (`claude-code-action`): `@claude` mention, modalità automation con `prompt`, setup rapido/manuale, permessi GitHub App, federazione OIDC. | **NUOVO — approfondito in §2.8** |
| `github-actions-cloud-providers.md` | Uso della GitHub Action con Bedrock/Google Cloud's Agent Platform/Microsoft Foundry invece della Claude API diretta. | Estensione della precedente, stesso perimetro |
| `github-enterprise-server.md` | Claude Code con GitHub Enterprise Server self-hosted: sessioni web, code review, marketplace plugin. | **NUOVO, enterprise** |
| `gitlab-ci-cd.md` | Integrazione CI/CD con GitLab. | **NUOVO — stesso pattern di github-actions ma per GitLab** |

### 1.8 Remoto, mobile, canali esterni

| Pagina | Sintesi | Copertura |
|---|---|---|
| `remote-control.md` | Continua una sessione **locale** da telefono/browser (claude.ai/code o app mobile). Esecuzione resta sulla macchina locale; solo lo streaming passa da server Anthropic. Trusted Devices (biometria) per Team/Enterprise. | **NUOVO — approfondito in §2.7, alta priorità** |
| `channels.md` | MCP server che inietta eventi (webhook, chat) in una sessione **già aperta**: Telegram/Discord/iMessage plugin ufficiali, allowlist mittenti, `--channels` flag, enterprise gate. | **NUOVO — approfondito in §2.7, alta priorità** |
| `channels-reference.md` | Reference tecnica per costruire un proprio channel server: contratto capability, eventi notifica, reply tool, permission relay. | **NUOVO, per sviluppatori di estensioni** |
| `claude-code-on-the-web.md` | Sessioni su infrastruttura cloud gestita da Anthropic (claude.ai/code): `--cloud`/`--teleport`, auto-fix PR, isolamento VM, condivisione sessioni. | **NUOVO — approfondito in §2.7, alta priorità** |
| `web-quickstart.md` | Onboarding rapido a Claude Code on the web: collega GitHub, invia un task, review PR senza setup locale. | Guida introduttiva, dettaglio assorbito in claude-code-on-the-web |
| `cloud-environments.md` | Config di sessioni cloud: livelli di accesso rete, variabili d'ambiente, setup script, caching ambiente. | **NUOVO — condiviso da routines/web/Claude Tag, vedi §2.7** |
| `slack.md` | Claude Code in Slack (versione "legacy", in dismissione per Team/Enterprise a favore di Claude Tag; resta il path per Pro/Max). | **NUOVO, minore** |
| `claude-tag.md` | "Claude Tag" — successore di Slack integration, rimanda a doc su claude.com (fuori da code.claude.com/docs). | **NUOVO, minore, doc esterna** |

### 1.9 Code review, sicurezza del codice, qualità

| Pagina | Sintesi | Copertura |
|---|---|---|
| `code-review.md` | Prodotto "Code Review": review PR automatiche multi-agente su GitHub, commenti inline per severità, `CLAUDE.md`+`REVIEW.md` per tuning, check run neutro (non blocca merge), `/code-review` locale. | **NUOVO — approfondito in §2.8, alta priorità** |
| `ultrareview.md` | `/code-review ultra`: review multi-agente più profonda, eseguita in cloud, per trovare/verificare bug prima del merge. | **NUOVO — estensione di code-review** |
| `claude-security.md` | Plugin "Claude Security": scansione vulnerabilità nel codebase durante una sessione, genera patch. | **NUOVO — vedi §2.11** |
| `security-guidance.md` | Plugin "security-guidance": review di sicurezza asincrona sulle proprie modifiche (già osservato in uso reale nella ground-truth locale del doc hooks). | **Parzialmente già noto (citato come esempio di `asyncRewake` hook), ma non descritto come prodotto — vedi §2.11** |

### 1.10 Output, personalizzazione dell'interazione

| Pagina | Sintesi | Copertura |
|---|---|---|
| `output-styles.md` | Modifica il system prompt (ruolo/tono/formato): built-in (Default/Proactive/Explanatory/Learning) + custom via Markdown con frontmatter (`keep-coding-instructions`, `force-for-plugin`). | **NUOVO — approfondito in §2.1, alta priorità** |
| `artifacts.md` | Pubblica output di sessione come pagina web interattiva privata/condivisa su claude.ai, con capability di chiamare MCP connector a runtime. | **NUOVO — approfondito in §2.7, alta priorità (rilevante anche perché il Control Plane stesso userà artifact-like output)** |

### 1.11 Sicurezza, sandboxing, enterprise policy

| Pagina | Sintesi | Copertura |
|---|---|---|
| `security.md` | Overview safeguard di sicurezza e best practice. | Introduttiva, dettagli nelle pagine specifiche sotto |
| `sandboxing.md` | Tool Bash sandboxato: isolamento filesystem/rete via OS (Seatbelt su macOS, namespace+seccomp su Linux/WSL2), `/sandbox` UI, `allowUnsandboxedCommands`. | **NUOVO — approfondito in §2.11, alta priorità (distinto dai "permessi" già documentati)** |
| `sandbox-environments.md` | Confronto tra opzioni di isolamento: sandbox Bash integrato, sandbox runtime, dev container, Docker, VM — quale scegliere per il proprio threat model. | **NUOVO — indice comparativo, assorbito in §2.11** |
| `zero-data-retention.md` | ZDR per Enterprise: scope, cosa NON copre (chat claude.ai, Cowork), feature disabilitate sotto ZDR (web, cloud session, Artifacts, feedback, Remote Control), Fable 5 non disponibile. | **NUOVO — approfondito in §2.11, alta priorità (impatta quali feature del Control Plane sono visualizzabili in org ZDR)** |
| `data-usage.md` | Policy di utilizzo dati Anthropic. | Riferimento normativo, non tecnico-funzionale |
| `admin-setup.md` | Decision map completa per admin: provider API, come le settings raggiungono i device (server-managed/plist/registry/file), cosa enforceare (permessi, sandbox, MCP, plugin, hook, login, modelli, versione), visibilità uso, data handling. | **NUOVO — approfondito in §2.11, altissima priorità (è la mappa mentale enterprise dell'intero prodotto)** |
| `server-managed-settings.md` | Config centralizzata via server (claude.ai admin console) senza bisogno di MDM. | **NUOVO — meccanismo di delivery citato in admin-setup, vedi §2.11** |
| `managed-mcp.md` | Allowlist/denylist di server MCP a livello enterprise. | Overlap parziale con §2.6 di hooks-mcp-permissions (che copre `allowedMcpServers` a livello di chiave settings), qui la pagina dedicata con più contesto |
| `network-config.md` | Config enterprise: proxy, CA custom, mTLS. | **NUOVO, enterprise infra** |
| `corporate-launcher.md` | Instrada i processi lanciati da Claude Code (incl. supervisor agent view) attraverso un launcher aziendale richiesto. | **NUOVO, enterprise, di nicchia** |
| `auto-mode-config.md` | Config del classifier di "auto mode": repo/bucket/domini fidati, override regole block/allow, ispezione config effettiva. | **NUOVO — dettaglio profondo di una feature (auto mode) solo accennata nel doc permessi esistente** |
| `legal-and-compliance.md` | Accordi legali, certificazioni di compliance, info di sicurezza. | Riferimento legale, non tecnico |

### 1.12 Osservabilità, costi, analytics

| Pagina | Sintesi | Copertura |
|---|---|---|
| `monitoring-usage.md` | OpenTelemetry: metriche, eventi, tracing (beta), 8 metriche + 15 tipi di evento + span hierarchy, redazione PII di default, `otelHeadersHelper`. | **NUOVO — approfondito in §2.11, il dettaglio OTel richiesto esplicitamente dal task, alta priorità** |
| `analytics.md` | Dashboard di analytics team: adoption, velocity, metriche di engagement. | **NUOVO — approfondito in §2.1 (cost/usage tracking)** |
| `costs.md` | `/usage`, spend limit, riduzione token usage, breakdown per skill/subagent/plugin/MCP server, background token usage. | **NUOVO — approfondito in §2.1, alta priorità (`/cost`/`/usage` esplicitamente richiesti)** |

### 1.13 Piattaforme cloud / deployment enterprise

| Pagina | Sintesi | Copertura |
|---|---|---|
| `amazon-bedrock.md` | Setup Claude Code su Amazon Bedrock: IAM, troubleshooting. | **NUOVO, provider-specific** |
| `google-vertex-ai.md` | Setup su Google Cloud's Agent Platform (ex Vertex AI). | **NUOVO, provider-specific** |
| `microsoft-foundry.md` | Setup su Microsoft Foundry. | **NUOVO, provider-specific** |
| `claude-platform-on-aws.md` | Claude API Anthropic-operated con auth AWS, controllo IAM, billing AWS Marketplace. | **NUOVO, provider-specific (diverso da Bedrock: qui è Anthropic a operare, AWS fa da billing/IAM layer)** |
| `third-party-integrations.md` | Overview enterprise deployment: confronto provider, autenticazione, regioni, parità feature. | Indice comparativo dei 4 provider sopra |

### 1.14 Gateway

| Pagina | Sintesi | Copertura |
|---|---|---|
| `gateways.md` | Overview: instradare Claude Code via gateway self-hosted per credenziali centralizzate, usage tracking, cost control. | **NUOVO — vedi §2.11** |
| `llm-gateway.md` | Gateway generico (es. LiteLLM) che l'organizzazione già gestisce. | **NUOVO** |
| `llm-gateway-connect.md` | Come puntare Claude Code al gateway dell'org (base URL, credenziali). | **NUOVO** |
| `llm-gateway-protocol.md` | Contratto API tra Claude Code e un gateway: endpoint, header, degradazione feature. | **NUOVO, per chi implementa gateway** |
| `llm-gateway-rollout.md` | Come deployare un gateway per l'intera org: config, credenziali dev, managed settings, verifica. | **NUOVO, enterprise ops** |
| `claude-apps-gateway.md` | Gateway "ufficiale" Anthropic self-hosted per Bedrock/Claude Platform on AWS/Google Cloud/Microsoft Foundry con SSO, controllo modelli per gruppo, telemetria OTLP. | **NUOVO — prodotto specifico, non solo un concetto generico** |
| `claude-apps-gateway-config.md` | Reference completa di `gateway.yaml`. | Dettaglio tecnico del gateway sopra |
| `claude-apps-gateway-deploy.md` | Deploy/operazioni: registrazione IdP, build container, K8s/Cloud Run, rotazione secret. | Dettaglio operativo |
| `claude-apps-gateway-on-aws.md` | Esempio concreto di deploy su AWS (ECS Fargate/EKS, RDS, Secrets Manager). | Esempio worked |
| `claude-apps-gateway-on-gcp.md` | Esempio concreto di deploy su Google Cloud (Cloud Run/GKE, Cloud SQL). | Esempio worked |
| `claude-apps-gateway-spend-limits.md` | Limiti di spesa per-developer via Admin API, enforcement live. | **NUOVO — rilevante per cost governance enterprise** |

### 1.15 Agent SDK (confine con Claude Code)

> Vedi **§2.12** per la trattazione unificata del confine Claude Code ↔ Agent SDK. Elenco pagine:

| Pagina | Sintesi |
|---|---|
| `agent-sdk/overview.md` | Cos'è l'SDK, confronto con CLI/Client SDK/Managed Agents, capability disponibili, branding guideline. |
| `agent-sdk/quickstart.md` | Primo agente SDK in Python/TypeScript. |
| `agent-sdk/agent-loop.md` | Come funziona il loop dell'agente: lifecycle messaggi, esecuzione tool, context window. |
| `agent-sdk/claude-code-features.md` | Come caricare istruzioni di progetto, skill, hook di Claude Code dentro un agente SDK. |
| `agent-sdk/cost-tracking.md` | Tracking costo/uso token nell'SDK, prompt caching. |
| `agent-sdk/custom-tools.md` | Tool custom via server MCP in-process. |
| `agent-sdk/file-checkpointing.md` | Checkpointing per SDK: traccia modifiche file, ripristina a stato precedente (equivalente SDK di `/rewind`). |
| `agent-sdk/hooks.md` | Hook nell'SDK (intercettare/customizzare comportamento). |
| `agent-sdk/hosting.md` | Deploy in produzione: architettura subprocess, persistenza sessione, scaling, isolamento multi-tenant, Docker/K8s/sandbox provider. |
| `agent-sdk/mcp.md` | Config MCP nell'SDK: transport, tool search, auth. |
| `agent-sdk/migration-guide.md` | Guida di migrazione da "Claude Code SDK" (nome storico) a "Claude Agent SDK". |
| `agent-sdk/modifying-system-prompts.md` | Preset `claude_code` vs system prompt custom, CLAUDE.md/output style/append. |
| `agent-sdk/observability.md` | Export OpenTelemetry per l'SDK. |
| `agent-sdk/permissions.md` | Permission mode, hook, regole allow/deny nell'SDK. |
| `agent-sdk/plugins.md` | Caricare plugin custom (skill/agent/hook/MCP) via SDK. |
| `agent-sdk/python.md` | Reference API completa Python SDK. |
| `agent-sdk/secure-deployment.md` | Guida sicurezza per deploy: isolamento, gestione credenziali, controlli rete. |
| `agent-sdk/session-storage.md` | Mirror dei transcript su S3/Redis/backend custom. |
| `agent-sdk/sessions.md` | Persistenza conversazione: continue/resume/fork. |
| `agent-sdk/skills.md` | Agent Skills nell'SDK. |
| `agent-sdk/slash-commands.md` | Comandi slash nell'SDK. **[GIÀ COPERTO nel doc skills-agents-commands.md, §3.2]** |
| `agent-sdk/streaming-output.md` | Risposte in tempo reale (streaming). |
| `agent-sdk/streaming-vs-single-mode.md` | Due modalità di input per l'SDK e quando usarle. |
| `agent-sdk/structured-outputs.md` | JSON validato via JSON Schema/Zod/Pydantic. |
| `agent-sdk/subagents.md` | Subagent nell'SDK. **[GIÀ COPERTO parzialmente nel doc skills-agents-commands.md, §2]** |
| `agent-sdk/todo-tracking.md` | Todo list nell'SDK. |
| `agent-sdk/tool-search.md` | Scaling a migliaia di tool con discovery on-demand. |
| `agent-sdk/troubleshooting.md` | Errori SDK mappati a causa/fix, per TS e Python. |
| `agent-sdk/typescript.md` | Reference API completa TypeScript SDK. |
| `agent-sdk/typescript-v2-preview.md` | Reference della V2 session API TypeScript, **rimossa** — documentata per chi ha ancora codice legacy. |
| `agent-sdk/user-input.md` | Come esporre richieste di approvazione/domande all'utente e restituire le decisioni all'SDK. |

### 1.16 Debug e diagnostica configurazione

| Pagina | Sintesi | Copertura |
|---|---|---|
| `debug-your-config.md` | Diagnosi di perché CLAUDE.md/settings/hook/MCP/skill non hanno effetto — usa `/context`, `/doctor`, `/hooks`, `/mcp`. | **NUOVO — pagina "meta" molto rilevante: è letteralmente la checklist diagnostica che un Control Plane dovrebbe automatizzare** |
| `errors.md` | Già citato in §1.1 — reference errori. | — |
| `troubleshooting.md` | Già citato in §1.1. | — |

---

## 2. Aree nuove approfondite — con valutazione Control Plane

Per ciascuna area: cosa fa, dettagli chiave verificati dalle fonti primarie, e **valutazione esplicita** se il Control Plane dovrebbe gestirla/visualizzarla.

### 2.1 Checkpoint/rewind, cost/usage tracking, output styles, extended thinking/effort

#### Checkpoint & rewind (`checkpointing.md`)

Claude Code cattura automaticamente uno snapshot dei file **prima di ogni prompt utente** (non ad ogni edit). Tiene i 100 checkpoint più recenti per sessione, salvati insieme alla conversazione (sopravvivono a `/resume`), cancellati dopo 30 giorni (`cleanupPeriodDays`). `/rewind` (o doppio `Esc` a prompt vuoto) apre un menu con 5 azioni: restore code+conversation, restore conversation only, restore code only, summarize from here, summarize up to here.

**Limiti importanti**: le modifiche fatte da comandi Bash (`rm`, `mv`, `cp`) **non sono tracciate**; le modifiche di un subagent in background **non sono ripristinate** dal rewind (serve git); i file symlinkati/hard-linked vengono **skippati** con warning esplicito. Non è un sostituto del version control — è "local undo" complementare a Git.

**Valutazione Control Plane: SÌ.** Un Control Plane che visualizza "attività di Claude Code" dovrebbe mostrare la timeline dei checkpoint per sessione (già esiste il dato in `~/.claude/projects/.../` insieme al transcript), permettere un rewind visuale con diff prima/dopo, e — soprattutto — segnalare visivamente quando un checkpoint **non copre** modifiche (bash, subagent) così l'utente non si affida erroneamente al rewind per quelle. È un caso d'uso naturale per una UI: attualmente è testuale/menu-driven nel terminale.

#### Cost & usage tracking (`costs.md`, `analytics.md`)

`/usage` mostra: costo/durata/token per modello della sessione corrente (azzerato da `/clear`), e — su piano Pro/Max/Team/Enterprise — un breakdown per **attribuzione** (percentuale di uso per skill, subagent, plugin, singolo MCP server) e **behavior flag** (es. "long context" o "cache miss" quando >10% dell'uso recente). A livello org: spend report CSV, Enterprise Analytics API, Claude Code Analytics API (Console), workspace spend limit. Su cloud provider (Bedrock/Google Cloud/Microsoft Foundry) l'unica via per attribuzione per-utente è OpenTelemetry o un Claude apps gateway con spend limit per-utente.

Da notare per il Control Plane: i dati di `/usage` sono **calcolati localmente da conteggi di token a prezzo di listino** — non riflettono sconti contrattuali, quindi per numeri "billing-accurate" serve la Console. Il breakdown per skill/subagent/plugin/MCP è però un dato molto ricco e strutturato, potenzialmente estraibile.

**Valutazione Control Plane: SÌ, con caveat.** Una dashboard di costo/utilizzo per skill/subagent/plugin/MCP è esattamente il tipo di vista che il terminale non offre bene (solo testo in `/usage`, azzerato ad ogni `/clear`). Il Control Plane potrebbe aggregare storicamente questi dati leggendo i transcript JSONL (`~/.claude/projects/<project>/<session-id>.jsonl`) o, meglio, ricevendoli via OpenTelemetry (vedi §2.11) per numeri persistenti e cross-sessione — l'approccio via OTel è **nettamente preferibile** al parsing dei JSONL, che sono un formato interno non garantito stabile tra versioni (lo dice esplicitamente `sessions.md`: "Entry format is internal to Claude Code and changes between versions").

#### Output styles (`output-styles.md`)

Modificano il **system prompt** (ruolo/tono/formato di risposta), non la conoscenza di Claude. 4 built-in: Default, Proactive (esecuzione autonoma più aggressiva del solo auto mode, ma senza bypassare i permessi), Explanatory (aggiunge "Insights" educativi), Learning (collaborativo, aggiunge marker `TODO(human)`). Custom output style: file Markdown in `~/.claude/output-styles`, `.claude/output-styles`, o dentro plugin (`output-styles/`), con frontmatter `name`, `description`, `keep-coding-instructions` (default `false` — se `true` mantiene le istruzioni SWE di base di Claude Code), `force-for-plugin` (solo per plugin: applica lo style automaticamente quando il plugin è abilitato). Selezione via `/config` → salvata in `.claude/settings.local.json` come chiave `outputStyle`. Cambio effettivo solo dopo `/clear` o nuova sessione (fa parte del system prompt, letto una sola volta).

Tabella di confronto ufficiale con feature simili: Output styles modifica il system prompt sempre; CLAUDE.md aggiunge un messaggio utente dopo il system prompt; `--append-system-prompt` appende senza rimuovere; Agent lancia un subagent con proprio system prompt; Skill carica istruzioni task-specific on-demand.

**Valutazione Control Plane: SÌ.** È un asse di configurazione distinto e completamente assente dai tre documenti esistenti (che coprono Skill/Subagent/Comandi, Hook/MCP/Permessi, Plugin/Marketplace). Un editor visuale per output style personalizzati (con anteprima del "voice/tone" risultante) e un selettore rapido per progetto sarebbero utili, specie perché la precedenza tra `.claude/output-styles/` annidati in monorepo segue una regola non ovvia (vince il più vicino alla cwd, dal v2.1.178).

#### Extended thinking / effort levels (`model-config.md`)

Cinque livelli di effort (`low`, `medium`, `high`, `xhigh`, `max`) — non tutti i modelli li supportano tutti (Opus 4.6/Sonnet 4.6 non hanno `xhigh`; modelli senza adaptive reasoning non hanno effort affatto). Default `high` (eccetto Opus 4.7 → `xhigh`). C'è anche `ultracode`, che non è un effort level del modello ma un **flag di Claude Code** che manda `xhigh` al modello e in più fa orchestrare a Claude i **dynamic workflow** (vedi §2.2) per task sostanziosi — sessione-only.

Il toggle "extended thinking" (Option+T / Alt+T) è distinto dall'effort level: controlla se il ragionamento avviene affatto (dove disponibile), mentre l'effort controlla quanto. Su modelli con **adaptive reasoning** (Fable 5, Sonnet 5, Opus 4.7+) il pensiero è sempre "opzionale per-step" e non disattivabile con `MAX_THINKING_TOKENS=0` (tranne parzialmente su Fable 5, dove non è mai disattivabile). Su modelli più vecchi (Opus 4.6/Sonnet 4.6) esiste ancora la modalità a **budget fisso** controllata da `MAX_THINKING_TOKENS`, attivabile con `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1`.

Le organizzazioni Enterprise possono impostare **effort limit per ruolo** (`organization effort limits`), indipendenti da `availableModels`.

**Valutazione Control Plane: SÌ, per la parte enterprise; FORSE per il resto.** Un pannello che mostri/imposti l'effort level per progetto/sessione ha senso, ma è già ben servito da `/effort` e `/model` nel terminale (bassa frizione). Il valore aggiunto reale per un Control Plane è **visibilità aggregata**: quali sessioni girano a `max`/`ultracode` (costoso), e — per admin — editing visuale degli `organization effort limits` per ruolo, che oggi richiede la Enterprise console di claude.ai (fuori da Claude Code stesso, quindi il Control Plane potrebbe fare da proxy/documentazione ma non da editor diretto salvo API admin dedicate).

#### Advisor tool (`advisor.md`, non fetchato per intero ma citato)

Abbina il modello principale a un modello "advisor" più forte, consultato da Claude in momenti chiave (alternativa più granulare a `opusplan`, che switcha modello solo al confine plan→execution). Config: `advisorModel` in settings, `--advisor` flag.

**Valutazione Control Plane: FORSE.** Feature di nicchia, configurazione singola (un campo). Visualizzabile in un pannello "Model & Reasoning" insieme a effort/thinking, ma non giustifica una sezione dedicata.

---

### 2.2 Multi-agente e parallelismo: agent view, agent teams, dynamic workflows, worktree

Questa è l'area probabilmente **più sotto-rappresentata** nei tre documenti esistenti (che trattano solo Subagent "singolo", invocato via tool `Agent`). Claude Code ha in realtà **quattro** meccanismi di parallelismo distinti, ciascuno con architettura propria:

| Meccanismo | Chi orchestra | Dove vive lo stato intermedio | Scala | Comando |
|---|---|---|---|---|
| Subagent (già documentato) | Claude, turno per turno | Context window di Claude | Pochi task delegati per turno | tool `Agent` |
| **Agent view** | L'utente (dispatcher manuale) | Sessioni background indipendenti | Fino a 32 sessioni concorrenti (`--capacity`) | `claude agents` |
| **Agent team** | Un agente "lead" tra pari | Task list condivisa + mailbox | Manciata di peer long-running | env var `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` poi linguaggio naturale |
| **Dynamic workflow** | Uno script JS | Variabili dello script | Fino a 1000 agent per run, 16 concorrenti | `ultracode` in prompt, `/effort ultracode`, o `/deep-research` |

**Agent view** (`agent-view.md`) — research preview. `claude agents` apre una tabella di sessioni raggruppate per stato (needs input / working / completed). Dispatch da CLI (`claude --bg`), da dentro una sessione (`/bg`, `/fork`), o dall'input di agent view stesso. Architettura: **un processo supervisor per-utente** (non per-progetto) che gestisce lifecycle e stato persistente in `~/.claude/jobs/<id>/`, sopravvive alla chiusura del terminale, si riavvia dopo update. Le sessioni background si spostano **automaticamente** in worktree isolati sotto `.claude/worktrees/` prima di editare file. Comandi shell: `claude agents --json`, `claude attach <id>`, `claude logs <id>`, `claude stop/respawn/rm <id>`, `claude daemon status/stop`. Disabilitabile con `disableAgentView` / `CLAUDE_CODE_DISABLE_AGENT_VIEW=1`.

**Agent team** (`agent-teams.md`) — sperimentale, **disabilitato di default**, richiede `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Un lead spawna teammate che comunicano **direttamente tra loro** (non solo report al lead) via mailbox JSON (`~/.claude/teams/{team-name}/inboxes/{agent}.json`) e una task list condivisa con dipendenze e file locking per il claim. Display mode: in-process (default) o split-pane (richiede tmux o iTerm2+`it2`). Limitazioni dichiarate: no resume di teammate in-process dopo `/resume`, no nested team, un solo team per sessione, permessi fissati allo spawn. Consumo token **significativamente più alto** di un subagent (ogni teammate è un'istanza Claude Code separata con proprio context window).

**Dynamic workflow** (`workflows.md`) — la feature concettualmente più "infrastrutturale": Claude scrive uno **script JavaScript** (`agent()`, `pipeline()`) che un runtime esegue **in background separato dalla conversazione**, con risultati intermedi che restano in variabili di script (mai nel context window di Claude). Questo è ciò che rende un workflow **resumable**: lo script viene salvato su disco (`~/.claude/projects/.../`) e rieseguito da dove interrotto (con regole precise su cosa viene rieseguito). Bundled: `/deep-research`. Salvabile come comando riusabile in `.claude/workflows/` (progetto) o `~/.claude/workflows/` (personale) — diventa `/nome-custom`. Un size guideline (`small`/`medium`/`large`/`unrestricted`) consiglia a Claude quanti agent generare. Governance: `disableWorkflows` in settings o toggle admin console.

**Worktree** (`worktrees.md`) — il meccanismo di isolamento file **sotto** a tutto quanto sopra. `--worktree <nome>` crea una copia isolata sotto `.claude/worktrees/<nome>/` su un nuovo branch `worktree-<nome>`. Claude Code applica **enforcement attivo**: blocca edit/comandi Bash che tentano di scrivere fuori dal worktree o redirect git verso il checkout principale. Un subagent può essere forzato in worktree con `isolation: worktree` in frontmatter (già noto dal doc skills-agents-commands, ma qui c'è il meccanismo di **cleanup automatico**: sweep periodico che rimuove worktree vuoti più vecchi di `cleanupPeriodDays`, mai quelli creati manualmente con `--worktree`).

**Valutazione Control Plane: SÌ, altissima priorità — è probabilmente il gap più importante rispetto ai tre doc esistenti.** Un Control Plane per "gestire l'attività di Claude Code" senza una vista su agent view/team/workflow coprirebbe solo il caso mono-sessione. Concretamente:
- **Agent view**: SÌ — dashboard multi-sessione è quasi un porting 1:1 di quello che agent view fa già in TUI; un Control Plane web è naturalmente superiore per questo (`claude agents --json` esiste già come fonte dati).
- **Agent team**: SÌ ma con cautela — è sperimentale/opt-in, quindi il Control Plane dovrebbe esporre il toggle e poi visualizzare mailbox/task list (dati già in JSON su disco), ma non investire troppo finché la feature non esce da research preview.
- **Dynamic workflow**: SÌ, alta priorità — la vista `/workflows` (fasi, agent count, token, drill-down) è esattamente il tipo di UI che beneficia di essere web-based invece che TUI. Il salvataggio come comando riusabile è un'azione change-management che il Control Plane dovrebbe esporre (elenco workflow salvati, chi li ha creati, quando rieseguiti).
- **Worktree**: FORSE come vista standalone — è più infrastruttura di supporto; ha senso mostrarla come dettaglio dentro le viste di agent view/team piuttosto che come sezione autonoma.

---

### 2.3 Gestione della memoria: CLAUDE.md avanzato, auto memory, context/compact

Il doc `memory.md` conferma e amplia quanto già accennato negli altri tre documenti (che citano `.claude/rules/` solo di striscio). Punti davvero nuovi:

**Auto memory** — sistema **separato** da CLAUDE.md: Claude stesso scrive note su cosa impara (comandi di build, insight di debug, preferenze) in `~/.claude/projects/<project>/memory/MEMORY.md` + file tematici, **senza intervento dell'utente**. Solo i primi 200 righe / 25KB di `MEMORY.md` vengono caricati ad ogni sessione; file tematici caricati on-demand. Condiviso tra tutti i worktree dello stesso repo, ma **non tra macchine**. Toggle `autoMemoryEnabled` (default `true`), path personalizzabile con `autoMemoryDirectory`. Frontmatter con timestamp `modified` (ISO 8601) per sapere quanto è "fresca" una nota. Visibile/editabile via `/memory`.

**`.claude/rules/` con `paths:` frontmatter** — regole scoped per pattern di file (es. solo quando Claude legge `src/api/**/*.ts`), caricate **on-demand** invece che sempre, con un budget di espansione (1000 pattern / 4MiB) per evitare crash su brace-expansion complesse. Supportano symlink per condividere regole tra progetti.

**`claudeMdExcludes`** — in monorepo grandi, esclude CLAUDE.md di altri team via glob su path assoluti, configurabile a qualunque livello di settings.

**Context window** (`context-window.md`) — pagina con simulazione interattiva (contenuto solo parzialmente estraibile via fetch testuale, ma la struttura è chiara): mostra visivamente cosa entra in context all'avvio (system prompt, auto memory, env info, MCP tool deferiti), cosa viene aggiunto durante il lavoro (file letti, rule scoped che scattano, hook `PostToolUse` con `additionalContext`), il comportamento dei subagent (context isolato, non visibile al padre tranne il summary finale), e cosa sopravvive a `/compact` (CLAUDE.md di root viene **ri-letto da disco e reiniettato**; CLAUDE.md annidati e rule path-scoped **non** vengono reiniettati automaticamente, si ricaricano solo quando Claude rilegge un file nella subdirectory pertinente).

**Valutazione Control Plane: SÌ per auto memory, FORSE per context window viz.**
- **Auto memory**: SÌ — è un sistema di stato persistente completamente nuovo, con file su disco strutturati (`MEMORY.md` + topic file + frontmatter `modified`), perfetto per una vista "cosa ha imparato Claude su questo progetto", con possibilità di audit/edit visuale (oggi richiede `/memory` da terminale). Interessante anche mostrare la history di come `MEMORY.md` cresce/si accorcia nel tempo (Claude Code stesso emette reminder quando il file è vicino al limite).
- **`.claude/rules/` con path-matching**: SÌ, per lo stesso motivo per cui il Control Plane gestirà già CLAUDE.md — una vista che mostri quali rule esistono, i loro pattern, e (idealmente) una simulazione "quali rule scatterebbero se Claude leggesse il file X" sarebbe di alto valore, dato che oggi questo è invisibile finché non succede in sessione.
- **Context window live viz**: FORSE — bella idea in astratto (mostrare in tempo reale cosa riempie il context di una sessione attiva), ma richiederebbe hook in tempo reale sul transcript JSONL di una sessione live, complessità non banale, e il valore marginale rispetto a `/context` nel terminale è discutibile finché non c'è un caso d'uso concreto (es. "sessione che sta per auto-compattare, intervieni").

---

### 2.4 Integrazioni IDE: VS Code, JetBrains

Sono **prodotti distinti** dal CLI, non semplici wrapper. Entrambi eseguono un server MCP interno locale chiamato `ide` (nascosto da `/mcp`), con cui la CLI comunica per: aprire diff nel viewer nativo, leggere la selezione corrente per `@`-mention, condividere diagnostici del linter/type-checker automaticamente. Trasporto: WebSocket **non cifrato** su loopback (`127.0.0.1`, porta random), autenticato con token in un lock file (`~/.claude/ide/<port>.lock`, permessi 0600) — la mancanza di TLS è dichiarata intenzionale ("il socket è loopback-only, quindi TLS non aggiungerebbe protezione").

**VS Code**: pannello grafico nativo (non solo terminale-in-tab), plan mode con documento Markdown apribile per commenti inline, gestione plugin **grafica** (`/plugins` apre un dialog con tab Plugins/Marketplaces — installazione, scope, abilitazione), gestione MCP via `/mcp` in-panel, **Focus view** (nasconde tool call/thinking dietro una riga espandibile per turno), integrazione Chrome (`@browser`), tool esposti al modello: `mcp__ide__getDiagnostics` (read-only) e **`mcp__ide__executeCode`** (esegue codice Python nel kernel Jupyter attivo — richiede sempre conferma umana via Quick Pick nativo, **distinta** dai permission hook `PreToolUse`). Alcune feature CLI-only restano non disponibili in VS Code: `!` bash shortcut, tab completion, tutti i comandi/skill (solo un sottoinsieme appare in `/`).

**JetBrains**: plugin che lancia `claude` nel terminale integrato dell'IDE (non bundla una propria copia della CLI, a differenza di VS Code) — quindi richiede l'installazione standalone della CLI **in aggiunta** al plugin. Stesse feature di base (diff viewer, selection sharing, diagnostic sharing) ma **nessun tool di esecuzione codice** esposto al modello (a differenza di VS Code/Jupyter). Configurazione WSL con dettagli di rete (mirrored networking o firewall rule) per risolvere "No available IDEs detected".

**Valutazione Control Plane: NO per gestione runtime, FORSE per configurazione statica.** Il Control Plane è pensato come web app che gestisce config/skill/MCP/agenti — le integrazioni IDE sono runtime UI competitor/complementari (VS Code ha già il proprio pannello grafico per plugin/MCP), quindi duplicare quella UX ha poco senso. Dove il Control Plane **può** aggiungere valore: (a) documentare/esporre le impostazioni extension-level di VS Code (`useTerminal`, `initialPermissionMode`, ecc. — sono in `settings.json` di VS Code, non in `~/.claude/settings.json`, quindi **fuori dal filesystem che il Control Plane presumibilmente already gestisce**) — probabilmente fuori scope; (b) segnalare all'utente, quando rilevante, che una config scritta dal Control Plane (es. un MCP server) sarà visibile anche da dentro VS Code/JetBrains via `/mcp`, per evitare confusione su "dove l'ho configurato". Non è un'area da costruire come sezione propria del Control Plane.

---

### 2.5 CLI/headless, variabili d'ambiente, modalità CI/CD

`headless.md` è il fondamento tecnico sia per script/CI sia per l'Agent SDK via CLI. Punti chiave:

- **`claude -p`** con **`--bare`** (raccomandato per script/SDK, diventerà default in futuro): salta auto-discovery di hook/skill/plugin/MCP/auto memory/CLAUDE.md, per risultati deterministici cross-macchina. In bare mode niente OAuth/keychain — serve `ANTHROPIC_API_KEY` esplicita.
- **`--output-format`**: `text` (default), `json` (con `total_cost_usd`, breakdown per modello), `stream-json` (NDJSON per streaming, con eventi `system/init`, `system/api_retry`, `system/plugin_install`).
- **`--json-schema`** per output strutturato validato.
- Gestione dei **subagent nello stream**: `parent_tool_use_id` per ricostruire l'albero di nesting; `--forward-subagent-text` per vedere anche il testo/thinking dei subagent (non solo tool_use/tool_result).
- Task in background terminati ~5s dopo la fine del turno (grace period), subagent/workflow in background invece attesi fino a 10 minuti (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`).
- `system/init` riporta plugin/MCP falliti al caricamento — pattern esplicito per **failare la CI** se un plugin/server non si carica (`plugin_errors`, `mcp_server_errors` array vuoti = tutto ok).

`env-vars.md` è la reference di tutte le variabili d'ambiente — trasversale a ogni altra pagina (molte già citate nei tre doc esistenti in forma sparsa: `CLAUDE_CODE_ENABLE_TELEMETRY`, `MAX_THINKING_TOKENS`, ecc.), ma qui è la fonte primaria completa non ancora consultata in blocco.

`cli-reference.md` è la reference di tutti i flag — anch'essa citata solo a spot nei tre doc precedenti (es. `--agents`), mai come pagina a sé.

**Valutazione Control Plane: SÌ per CI/CD status, FORSE per reference statiche.**
- **Headless/CI status monitoring**: SÌ — se il Control Plane vuole "gestire l'attività di Claude Code" a 360°, dovrebbe includere una vista sulle esecuzioni non interattive (CI, script schedulati) leggendo gli eventi `system/init`/`plugin_install`/`mcp_server_errors` da `stream-json` quando disponibili, per dare visibilità su "quali plugin/MCP falliscono silenziosamente in CI" — oggi invisibile a meno di grep dei log.
- **`env-vars.md`/`cli-reference.md` come reference**: FORSE — utili come pannello "cheat sheet" ricercabile nel Control Plane (specie `env-vars.md`, che è enorme e sparsa nei tre doc esistenti), ma è documentazione statica, non stato/config da gestire attivamente. Valore come feature di ricerca/lookup, non come area di gestione.

---

### 2.6 Scorciatoie da tastiera e customizzazione tastiera

`interactive-mode.md` (reference completa keybinding di default, organizzata per contesto: General, editing, history, ecc.) e `keybindings.md` (come **rimapparle**) sono un sistema completo e non banale:

- **19 contesti** (`Global`, `Chat`, `Autocomplete`, `Settings`, `Confirmation`, `Tabs`, `Transcript`, `HistorySearch`, `Task`, `ThemePicker`, `Attachments`, `Footer`, `MessageSelector`, `DiffDialog`, `ModelPicker`, `Select`, `Plugin`, `Scroll`, più `Voice` quando dictation è attiva).
- File `~/.claude/keybindings.json` con array `bindings`, ognuno scoped a un context; azione in formato `namespace:action`; `null` per unbind. Chord (`ctrl+k ctrl+s`) supportati. Rilevamento live senza restart.
- Shortcut riservati non rimappabili: Ctrl+C, Ctrl+D, Ctrl+M, Caps Lock.
- Conflitti noti con tmux (Ctrl+B), screen (Ctrl+A), SIGTSTP (Ctrl+Z).
- Validazione a caricamento con warning su parse error/context invalido/conflitti riservati/duplicati (visibili solo con `--debug`).

**Valutazione Control Plane: NO come area prioritaria, FORSE come editor visuale di comodità.** È una feature di produttività terminale pura, non tocca config/skill/MCP/agenti nel senso del mandato del Control Plane. Un editor visuale JSON per `keybindings.json` con validazione (evitando di dover lanciare `--debug` per trovare errori di sintassi) sarebbe una piccola utility gradevole ma bassa priorità — nessun impatto su governance/sicurezza/orchestrazione.

---

### 2.7 Automazione programmata, remoto e canali esterni (l'area "always-on" del prodotto)

Questa è la seconda area, dopo il multi-agente (§2.2), dove i tre documenti esistenti hanno una copertura pressoché nulla ma che rappresenta l'evoluzione più recente e strategica del prodotto: portare Claude Code fuori dalla sessione terminale interattiva sincrona.

**Tabella di confronto ufficiale** (da `remote-control.md`), riorganizzata:

| Meccanismo | Trigger | Dove gira Claude | Setup | Caso d'uso |
|---|---|---|---|---|
| Dispatch (Desktop) | Messaggio da app mobile | Macchina locale (Desktop) | Pairing app↔Desktop | Delegare mentre sei fuori |
| **Remote Control** | Steering da claude.ai/code o app mobile | Macchina locale (CLI/VS Code) | `claude remote-control` | Continuare a pilotare da un altro device |
| **Channels** | Evento push da Telegram/Discord/webhook | Macchina locale (CLI) | Plugin channel + `--channels` | Reagire a eventi esterni mentre sei via |
| Claude Tag/Slack | `@Claude` in team chat | Cloud Anthropic | Install app Slack | PR/review da chat di team |
| **Routines** | Schedule / API / evento GitHub | Cloud Anthropic (VM gestita) | claude.ai/code/routines o `/schedule` | Automazione ricorrente always-on |
| Scheduled tasks (`/loop`) | Intervallo dentro sessione aperta | Macchina locale, **solo mentre la sessione resta aperta** | `/loop` | Polling rapido in sessione |
| Desktop scheduled tasks | Cron locale | Macchina locale (Desktop) | UI Desktop | Automazione locale ricorrente |

**Routines** (`routines.md`) — la feature più "control-plane-shaped" dell'intero prodotto: una routine è **prompt + repo + connector**, salvata sull'account claude.ai, eseguita su infrastruttura gestita Anthropic (quindi **sopravvive al laptop chiuso**). Tre tipi di trigger combinabili: **schedule** (cron, min 1h, o one-off), **API** (endpoint HTTP dedicato per routine con bearer token, payload `text` esplicitamente wrappato come "untrusted data" per prevenire prompt injection dal chiamante), **GitHub event** (PR/release, con filtri su autore/branch/label/draft/merged, operatore regex). Gestibile da web (`claude.ai/code/routines`), Desktop, o CLI (`/schedule`, solo per trigger schedule — API/GitHub richiedono la UI web). **Non condivisa col team** — è personale, e le sue azioni (commit, PR, messaggi Slack) appaiono **come l'utente proprietario**. Cap giornaliero di run (eccetto i one-off).

**Remote Control** (`remote-control.md`) — a differenza di Claude Code on the web, **non è cloud**: la sessione gira sulla macchina locale (filesystem, MCP, tool tutti locali), solo lo **streaming** passa da server Anthropic (mai porte in ingresso aperte). Modalità: server mode (`claude remote-control`, multi-sessione, con `--spawn` worktree/same-dir/session), interactive mode (`--remote-control`), o attach da sessione esistente (`/remote-control`). **Trusted Devices** (beta, Team/Enterprise): richiede enrollment biometrico device + login <18h per poter vedere/steer una sessione da remoto — livello di sicurezza aggiuntivo separato dal semplice login account.

**Channels** (`channels.md`) — meccanismo per **iniettare eventi in una sessione già aperta**, non per crearne una nuova. Modellato come plugin MCP (Telegram/Discord/iMessage ufficiali, o custom via `channels-reference.md`), con **allowlist per mittente** (pairing code) e gate a livello organizzazione (`channelsEnabled`, `allowedChannelPlugins`). Ogni evento arriva come blocco `<channel source="...">`, distinto testualmente da un prompt utente diretto. Ancora in research preview.

**Claude Code on the web / cloud environments** (`claude-code-on-the-web.md`, `cloud-environments.md`) — sessioni **completamente cloud** (VM isolate Anthropic-managed), con `--cloud`/`--teleport` per spostare lavoro tra locale↔cloud, **auto-fix PR** (Claude osserva check CI e commenti di review su una PR e pusha fix automaticamente, con distinzione tra fix "chiari" applicati subito e richieste "ambigue" che chiedono conferma). Ogni sessione cloud usa un `cloud environment` — config condivisa (network access level: Trusted/Custom/Full, env var, setup script cacheable) usata anche da routines e Claude Tag.

**Artifacts** (`artifacts.md`) — pagine HTML/Markdown pubblicate come URL live su claude.ai, con CSP rigida (niente richieste esterne salvo chiamate a **MCP connector** dichiarate esplicitamente, che girano con le credenziali del **viewer**, non del publisher — quindi due persone che aprono lo stesso artifact possono vedere dati diversi). Sharing: privato / org (Team/Enterprise) / pubblico (Pro/Max, o Team/Enterprise se un Owner abilita "External sharing"). Gestibile anche da API Compliance (`GET/DELETE /v1/compliance/code/artifacts`).

**Valutazione Control Plane: SÌ su tutta la linea, priorità molto alta.** Questa è l'area dove un Control Plane aggiunge il valore più alto rispetto al terminale, perché:
- **Routines**: SÌ, priorità massima — oggi la gestione è sparsa tra web UI claude.ai e `/schedule` CLI (solo per lo schedule trigger); un Control Plane che aggrega **tutte** le routine dell'utente/org, il loro trigger, l'ultimo run, il costo, e permette editing visuale di `REVIEW.md`-equivalenti/prompt sarebbe di alto valore. Nota: le routine sono **account-level su claude.ai**, non filesystem-level — quindi il Control Plane dovrebbe integrare l'API Compliance/Enterprise Analytics piuttosto che leggere file locali, il che è un cambio architetturale rispetto a "leggere `~/.claude/`".
- **Remote Control**: SÌ — visibilità su quali sessioni locali sono esposte via Remote Control, con quale Trusted Device policy, è rilevante per audit di sicurezza enterprise.
- **Channels**: SÌ — allowlist mittenti e quali plugin channel sono attivi per sessione sono dati di sicurezza (chi può iniettare eventi in una sessione Claude) che meritano un pannello dedicato, specie lato admin (`allowedChannelPlugins`).
- **Artifacts**: SÌ per governance (retention, sharing pubblico on/off, audit log `claude_artifact_*`), meno per la creazione stessa (che resta un'azione naturale da dentro una sessione Claude).
- **Cloud environments**: SÌ — è la config condivisa da routine/web/Claude Tag, quindi un editor visuale di network access/env var/setup script è centrale.

**Nota architetturale per il Control Plane**: gran parte di questa area (routines, artifacts, cloud environments, analytics) vive **sull'account claude.ai**, non nel filesystem locale (`~/.claude/`) che presumibilmente è la fonte dati primaria pensata finora per il Control Plane. Questo apre una domanda di design esplicita: il Control Plane deve autenticarsi come client OAuth verso l'account claude.ai/Enterprise Analytics API per queste viste, oltre a leggere `~/.claude/*`? Vedi §3.

---

### 2.8 Code Review, ultrareview, GitHub/GitLab CI

**Code Review** (`code-review.md`) è un **prodotto separato** da GitHub Actions (`claude-code-action`), gestito come servizio managed: un Owner lo abilita per org (richiede Team/Enterprise, non disponibile con ZDR), sceglie i repo e il **trigger per repo** (once-after-open / after-every-push / manual). Review multi-agente in parallelo, con step di verifica per ridurre falsi positivi, output come commenti inline + check run `Claude Code Review` **sempre neutro** (non blocca mai il merge via branch protection — se si vuole gating, bisogna leggere l'ultima riga machine-readable del check run text via `gh`+`jq`). Tuning via due file distinti: `CLAUDE.md` (letto come contesto, violazioni = nit) e **`REVIEW.md`** (iniettato come istruzione a massima priorità in ogni agente della pipeline — non supporta `@import`). Pricing: $15-25 a review in media, fatturato separatamente su usage credits.

**Ultrareview** (`ultrareview.md`, non fetchato per intero ma ampiamente citato da `code-review.md`) — `/code-review ultra` esegue la review in cloud (non localmente), utile per bug-hunting più profondo prima del merge; richiede login claude.ai, non disponibile su Bedrock/Google Cloud/Microsoft Foundry né con ZDR.

**GitHub Actions** (`github-actions.md`) è invece un'action **che l'utente configura nei propri workflow YAML**, non un servizio managed: due modalità (interactive, risponde a `@claude`; automation, con `prompt` fisso in YAML per cron/eventi). Autenticazione via secret repo (`ANTHROPIC_API_KEY` o `CLAUDE_CODE_OAUTH_TOKEN`), o via **workload identity federation** (OIDC, nessun secret long-lived) per rollout a livello org. Distinto in modo netto da Code Review: qui l'utente scrive il workflow, controlla `claude_args`/plugin/prompt.

**GitLab CI/CD** (`gitlab-ci-cd.md`) — stesso pattern di GitHub Actions ma per pipeline GitLab.

**GitHub Enterprise Server** (`github-enterprise-server.md`) — supporto per repo self-hosted, con implicazioni su quali feature (sessioni web, code review, marketplace) restano disponibili.

**Valutazione Control Plane: SÌ per governance, FORSE per creazione workflow.**
- **Code Review (prodotto managed)**: SÌ — è config org-level (repo abilitati, trigger per repo, `REVIEW.md` per repo, spend cap) esattamente del tipo che un Control Plane admin-facing dovrebbe visualizzare/editare, con dashboard di costo/finding aggregati (l'endpoint analytics esiste già: `claude.ai/analytics/code-review`).
- **GitHub Actions/GitLab CI**: FORSE — sono file YAML nel repo del progetto, gestiti meglio come codice versionato che come stato in un Control Plane; il valore aggiunto sarebbe un **generatore/validator** di workflow YAML (scaffold `claude.yml` corretto) più che una vista "live" persistente.
- **Ultrareview**: FORSE — singola azione on-demand, poco stato da gestire oltre al link al risultato.

---

### 2.9 Sandboxing, sicurezza runtime, enterprise policy (oltre a Permessi già documentati)

Da distinguere nettamente da quanto già in `hooks-mcp-permissions.md` (che copre le **regole di permesso** allow/deny/ask): il **sandboxing** (`sandboxing.md`, `sandbox-environments.md`) è un layer di **enforcement OS-level** ortogonale, che agisce solo sul tool Bash (e processi figli), non sugli altri tool.

Meccanismo: su macOS usa il framework Seatbelt nativo (nulla da installare); su Linux/WSL2 richiede due pacchetti di sistema (namespace + seccomp filter opzionale). `/sandbox` apre un pannello con tab Mode/Overrides/Dependencies. Con sandboxing attivo, i comandi Bash girano con **allowlist di filesystem e domini di rete** enforced dal kernel — non più solo "chiedi il permesso", ma "impossibile accedere anche se il permesso fosse dato". `allowUnsandboxedCommands` controlla il fallback quando un comando fallisce sotto sandbox. Rilevante: `autoAllowBashIfSandboxed` (già citato nel doc permessi esistente) fa sì che un comando sandboxed passi **senza prompt** anche con una regola `ask` generica — il sandbox **sostituisce** quel prompt.

`sandbox-environments.md` è l'indice comparativo: sandbox Bash integrato vs sandbox runtime vs dev container vs Docker vs VM — quale scegliere per il proprio threat model, complementare non sovrapposto.

`admin-setup.md` è la **mappa mentale enterprise** dell'intero prodotto — non introduce meccanismi nuovi rispetto a quanto già nei tre doc (permessi, hook, MCP, plugin sono tutti già coperti nel dettaglio), ma li **organizza** in una checklist decisionale a 5 punti (provider → delivery settings → cosa enforceare → visibilità uso → data handling) con una tabella "Decide what to enforce" che elenca **17 controlli** con le relative chiavi settings — utile come blueprint di navigazione per un pannello admin del Control Plane, anche se il contenuto delle singole chiavi è già documentato altrove.

`zero-data-retention.md` — rilevante perché **disabilita esplicitamente** intere feature lato backend indipendentemente dal client: Claude Code on the Web, Cloud sessions da Desktop, **Artifacts**, feedback (`/feedback`,`/bug`,`/share`), **Remote Control**. Questo significa che un Control Plane che mostra pannelli per queste feature deve **rilevare lo stato ZDR dell'org** e nascondere/disabilitare coerentemente quei pannelli, altrimenti mostra funzionalità che falliranno silenziosamente lato server.

`auto-mode-config.md` — approfondisce "auto mode" (già citato nel doc permessi come uno dei 6 permission mode) con la configurazione del **classifier**: repo/bucket/domini fidati dall'org, override delle regole di block/allow di default, subcommand CLI per ispezionare la config effettiva.

`network-config.md`, `corporate-launcher.md` — infrastruttura enterprise (proxy, CA custom, mTLS; wrapping dei processi lanciati da Claude Code incluso il supervisor di agent view) — di nicchia ma con impatto diretto su deployment enterprise del Control Plane stesso, se il Control Plane girerà su reti aziendali con questi vincoli.

**Valutazione Control Plane: SÌ per sandboxing, SÌ per ZDR-awareness, FORSE per network/launcher.**
- **Sandboxing**: SÌ — è uno strato di sicurezza distinto e potente (enforcement kernel-level vs regole software), attualmente configurato solo via `/sandbox` TUI; un editor visuale di allowlist filesystem/rete con "simula questo comando: sarebbe bloccato?" sarebbe alto valore, specie perché la doc segnala esplicitamente confusione frequente ("Denying WebFetch blocca il tool fetch di Claude, ma se Bash è permesso, `curl`/`wget` possono ancora raggiungere qualunque URL — il sandboxing chiude questo gap").
- **ZDR-awareness**: SÌ, obbligatorio — non è una feature da "gestire" ma un **vincolo trasversale** che il Control Plane deve rispettare/rilevare per non promettere funzionalità che il backend rifiuterà.
- **`admin-setup.md` come blueprint**: SÌ come **struttura di navigazione** (i.e. organizzare le sezioni del Control Plane secondo questi 5 macro-controlli), non come nuovo contenuto da documentare.
- **Network config/corporate launcher**: FORSE — rilevanti solo per deployment enterprise del Control Plane stesso su reti con proxy/mTLS; non è "contenuto da gestire" ma "vincolo di deployment".

---

### 2.10 OpenTelemetry — dettaglio oltre quanto già noto

I tre documenti esistenti non trattano OpenTelemetry (non menzionato). `monitoring-usage.md` è quindi interamente nuovo. Sintesi struttrata (già estratta per intero in fase di ricerca):

- **Opt-in esplicito**: `CLAUDE_CODE_ENABLE_TELEMETRY=1`, poi exporter separati per metrics/logs/traces (`otlp`, `console`, `prometheus` solo per metrics, `none`).
- **8 metriche**: `session.count`, `lines_of_code.count`, `pull_request.count`, `commit.count`, `cost.usage`, `token.usage`, `code_edit_tool.decision`, `active_time.total` — con attributi specifici per metrica (es. `query_source: main|subagent|auxiliary`, `agent.name` redatto a `custom` se non built-in).
- **15 tipi di evento** (`claude_code.user_prompt`, `.api_request`, `.tool_result`, `.tool_decision`, `.mcp_server_connection`, `.plugin_installed`, `.plugin_loaded`, ecc.), correlabili tramite `prompt.id` condiviso — permette di ricostruire l'intera catena di un singolo turno (prompt → richieste API → tool call) in un backend esterno.
- **Tracing distribuito (beta)**: span hierarchy `interaction → llm_request/hook/tool → tool.execution`, propagazione W3C traceparent verso subprocessi Bash, richieste modello, MCP HTTP.
- **Redazione PII di default**: prompt utente, risposte, dettagli tool, body raw — tutti `<REDACTED>` finché non abilitati esplicitamente (`OTEL_LOG_USER_PROMPTS`, `OTEL_LOG_TOOL_DETAILS`, ecc.). Nomi di agent/skill/plugin **custom** dell'utente sono redatti a `custom`/`third-party`; solo quelli built-in/marketplace ufficiale appaiono in chiaro — un dettaglio di design privacy non ovvio.
- Gestibile centralmente via `env` block in managed settings (bloccato per l'utente).

**Valutazione Control Plane: SÌ, ma come *consumer* non produttore.** Il Control Plane non deve reimplementare OTel — deve piuttosto **essere un collector/dashboard** che riceve questi dati (o li legge da un backend OTel esistente come Prometheus/Grafana) per costruire le viste di costo/uso aggregate discusse in §2.1. Vale la pena che il Control Plane esponga un **wizard di setup OTel** (genera lo snippet `env` per `settings.json`, scegliendo exporter/endpoint) più che tentare di duplicare la pipeline di telemetria stessa. Questo è probabilmente **l'approccio architetturale più robusto** per tutta la sezione costi/uso (§2.1), preferibile al parsing dei JSONL locali.

---

### 2.11 Claude Code vs Agent SDK — dove passa il confine

Fonte primaria: `agent-sdk/overview.md` + `features-overview.md`. Il confine è **esplicito e ben definito** nella documentazione ufficiale, non ambiguo come poteva sembrare:

> "An agent is an application that completes a task by planning its own steps and calling tools... The Agent SDK gives you the same tools, agent loop, and context management that power Claude Code, programmable in Python and TypeScript."

Tabella ufficiale di scelta (riportata perché è la fonte di verità sul confine):

| Se stai... | Usa | Perché |
|---|---|---|
| Costruendo un agente senza reimplementare il tool loop | **Agent SDK** | Libreria che gira il loop nel tuo processo, Python o TypeScript |
| Sviluppo interattivo o task one-off da terminale | **Claude Code CLI** | Interfaccia terminale per uso quotidiano interattivo |
| Chiamando l'API direttamente, implementando tu il tool loop | **Client SDK** (Anthropic API) | Accesso diretto all'API Anthropic, non a Claude Code |
| Agenti long-running/asincroni senza gestire sandbox/sessioni tue | **Managed Agents** | API REST hosted, prodotto **separato** dall'Agent SDK — Anthropic gestisce agente e sandbox |

**Punti chiave per capire il confine:**
1. **Agent SDK ≠ Claude Code CLI**, ma **Claude Code CLI è costruito sopra le stesse fondamenta** (agent loop, tool nativi, gestione contesto) che l'SDK espone come libreria. La CLI è "un'app" costruita con quelle fondamenta; l'SDK è "le fondamenta stesse", riusabili per costruire app diverse.
2. **`claude -p` è il ponte**: per linguaggi diversi da Python/TypeScript (unici supportati nativamente dall'SDK), la via ufficiale è lanciare la CLI come subprocess con `-p --output-format json` — quindi anche chi non usa Python/TS "usa l'SDK" concettualmente, solo attraverso il binario CLI invece che import di libreria.
3. **Capacità 1:1**: tool nativi, hook, subagent, MCP, permessi, sessioni, skill/comandi/memoria (caricati automaticamente da `.claude/` e `~/.claude/` **esattamente come Claude Code**), plugin — sono tutte disponibili nell'SDK. Non è un sottoinsieme minimale, è la stessa piattaforma esposta programmaticamente.
4. **Vincolo di branding esplicito**: prodotti costruiti sull'Agent SDK **non possono chiamarsi "Claude Code" o "Claude Code Agent"**, né usare ASCII art che imiti Claude Code — devono avere un proprio brand ("Claude Agent" è l'unico termine "Claude"-branded consentito senza restrizioni). Inoltre, **non è consentito** offrire login claude.ai o rate limit di claude.ai a sviluppatori terzi tramite prodotti costruiti sull'SDK (salvo approvazione preventiva) — obbliga all'uso di API key.
5. **Managed Agents è un quarto prodotto**, distinto anche dall'Agent SDK: REST API hosted dove Anthropic gestisce sia l'agente sia il sandbox — non è nemmeno una libreria, è un servizio.

**`features-overview.md`** aggiunge il framework "quando usare cosa" **dentro** Claude Code stesso (CLAUDE.md vs Skill vs Subagent vs Hook vs MCP vs Plugin vs Agent team vs Workflow), con tabelle di confronto a coppie molto dettagliate — questo contenuto in realtà **sovrappone e consolida** quanto già nei tre doc esistenti (non introduce meccanismi nuovi) ma lo fa con un framing didattico ("build your setup over time": trigger → quale feature aggiungere) che potrebbe essere utile come **testo guida in-UI** del Control Plane per aiutare l'utente a scegliere il meccanismo giusto quando crea una nuova risorsa.

**Valutazione Control Plane: chiarimento concettuale, non una feature da costruire.** Il Control Plane, per definizione (gestisce Claude Code: skill/MCP/agenti/attività), **non è un client dell'Agent SDK** — è più corretto pensarlo come un **tool di configurazione e osservabilità per installazioni di Claude Code CLI/Desktop**, il cui backend potrebbe *eventualmente* usare l'Agent SDK per orchestrare le proprie chiamate (es. per interrogare Claude a supporto di feature del Control Plane stesso), ma la superficie che gestisce (settings.json, `.claude/skills/`, `.mcp.json`, sessioni, plugin) è quella del **prodotto Claude Code**, non quella dell'SDK. Vale la pena che il Control Plane **citi esplicitamente questa distinzione in UI** (es. un tooltip "Per costruire un agente custom da zero con queste stesse fondamenta, vedi Agent SDK — funzionalità diversa da questo pannello") per evitare confusione utente, ma non richiede di implementare pagine "Agent SDK" nel Control Plane.

---

### 2.12 Sicurezza applicativa: Claude Security, security-guidance

`claude-security.md` (plugin "Claude Security" — scansiona il codebase per vulnerabilità **on-demand durante una sessione**, produce patch da rivedere) e `security-guidance.md` (plugin "security-guidance" — review **asincrona** delle proprie modifiche via hook `PostToolUse`/`Stop` con pattern `asyncRewake`, già osservato **in uso reale** nella ground-truth del doc hooks esistente, ma lì trattato solo come "esempio di hook asincrono", non come prodotto a sé) sono entrambi plugin ufficiali con scopo di security scanning, distinti da Code Review (che è specifico per PR review) e da `security.md` (overview generica).

**Valutazione Control Plane: FORSE.** Sono plugin come tanti altri — già coperti concettualmente dal meccanismo "plugin" del doc `plugins-marketplace-config.md`. Il valore aggiunto di trattarli come sezione a sé nel Control Plane sarebbe basso; meglio un tag/categoria "security" nel catalogo plugin visualizzato dal Control Plane, con eventualmente una vista aggregata "findings di sicurezza recenti" se questi plugin scrivono output strutturato riutilizzabile (da verificare nella loro implementazione specifica, non documentato a questo livello).

---

## 3. Sintesi — domande di design aperte per chi prosegue

In ordine di priorità, basato sulle valutazioni sopra:

1. **Il Control Plane deve integrarsi con l'account claude.ai (OAuth/Enterprise Analytics API), non solo con il filesystem locale `~/.claude/`?** Routines, Artifacts, Analytics dashboard, Code Review (prodotto managed), e in parte Remote Control vivono **lato server Anthropic**, non in file locali. Questo è un cambio architetturale rispetto a un Control Plane che si limita a leggere/scrivere `settings.json`/`.claude/skills/` ecc. — va deciso esplicitamente se il perimetro include questa integrazione account-level o resta filesystem-only (nel qual caso Routines/Artifacts/Analytics vanno depriorizzati o trattati come "link esterni" invece che pannelli nativi).

2. **Multi-agente (agent view / agent team / dynamic workflow) è probabilmente il gap di prodotto più grande da colmare**: i tre doc esistenti coprono solo il Subagent "classico" (delega singola dentro una conversazione). Le tre feature nuove (§2.2) rappresentano l'evoluzione recente del prodotto verso il parallelismo reale, e sono tutte "TUI-shaped" oggi — cioè feature che una web app rimpiazzerebbe naturalmente meglio (tabelle multi-sessione, drill-down su fasi/agenti, split view). Vale la pena una fase di design dedicata.

3. **Cost/usage tracking**: l'approccio via **OpenTelemetry** (Control Plane come collector/dashboard, con wizard di setup) è preferibile al parsing dei transcript JSONL locali, dichiarati esplicitamente "formato interno, non garantito stabile tra versioni". Decisione di design: costruire il Control Plane come OTel collector integrato, o assumere un backend OTel esterno (Prometheus/Grafana) e limitarsi a fare da wizard di configurazione + eventuale proxy di query?

4. **ZDR-awareness come vincolo trasversale obbligatorio**: qualunque pannello che tocchi Artifacts/Cloud sessions/Remote Control/feedback deve rilevare lo stato ZDR dell'organizzazione e disabilitarsi coerentemente — da modellare come un flag globale nello stato del Control Plane, non caso per caso.

5. **Auto memory come nuova superficie di stato da gestire**: `~/.claude/projects/<project>/memory/` è un sistema di file strutturati (MEMORY.md + topic file + frontmatter `modified`) completamente nuovo rispetto a quanto già coperto — merita una vista dedicata (audit, edit, storia di crescita) simile a quella già pensata per CLAUDE.md.

6. **Sandboxing come strato di sicurezza distinto dai permessi** già documentati: editor visuale per allowlist filesystem/rete enforced a livello OS, con "simulatore" di cosa verrebbe bloccato — alto valore percepito, poco sforzo di design aggiuntivo (riusa pattern già previsti per i permessi).

7. **Confine Claude Code / Agent SDK**: non richiede feature nuove nel Control Plane, ma va **comunicato esplicitamente in UI** per evitare che gli utenti si aspettino di poter "costruire un agente SDK" dal Control Plane quando in realtà gestisce installazioni Claude Code.
