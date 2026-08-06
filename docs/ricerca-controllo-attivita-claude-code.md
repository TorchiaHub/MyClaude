# Ricerca: controllo attività Claude Code — globale vs workflow di progetto

Elementi essenziali da conoscere prima di procedere con l'implementazione del Control Plane.

## 1. Enforcement: le regole vanno imposte con Hooks/permissions, non con prompt

Gli hook di Claude Code sono comandi shell deterministici agganciati al ciclo di vita (es. `PreToolUse` può **bloccare** una tool call, forzare un prompt o farla proseguire) — a differenza di skill/custom command, girano *sempre*, non dipendono dal fatto che il modello segua un'istruzione. Se una regola deve essere realmente vincolante, va implementata come hook o permission, non come testo in `CLAUDE.md`.

**Impatto sul progetto:** quando il control plane genera/attiva un profilo, le regole "dure" (es. blocco comandi pericolosi) devono tradursi in voci `hooks`/`permissions` reali, non solo in istruzioni testuali nel prompt della recipe.

## 2. Telemetria nativa via OpenTelemetry — da valutare come alternativa al parsing dei `.jsonl`

Claude Code supporta l'export nativo di metriche, eventi/log (e opzionalmente trace) verso un backend OTel esterno: uso, costo, attività sui tool, cambi di permission-mode, errori API, connessioni MCP, eventi hook. **Prima di costruire da zero il parser dei transcript** (come previsto in DESIGN.md), va valutato se agganciarsi a OTel copre già gran parte del Token & Cost Dashboard e del Live Activity Monitor con meno lavoro e più stabilità (l'export OTel è un'API pensata per questo, il parsing dei `.jsonl` no).

## 3. Gerarchia permessi: attenzione a un bug noto nel merge

I settings (user/project/local) normalmente si **fondono** (gli array di permission si sommano), con priorità: `deny` > `ask` > `allow`, e a parità di tipo vince la regola più specifica. **Ma** è un problema noto che quando Claude Code crea `settings.local.json` in un progetto, l'oggetto `permissions` risultante **sovrascrive interamente** quello globale (incluso `defaultMode`), invece di fondersi.

**Impatto sul progetto:** se il Configuration & Profile Manager scrive/attiva profili modificando `settings.local.json`, deve tenerne conto esplicitamente (es. avvisare l'utente, o scrivere sempre l'unione esplicita invece di assumere il merge automatico).

## 4. Gestione multi-sessione: le assunzioni classiche non reggono

Una sessione agentica può durare ore mantenendo memoria/contesto/decisioni evolutive — rompe le assunzioni tipiche di reverse proxy/API gateway. Per un controllo efficace a livello multi-sessione servono, concettualmente: allowlist/denylist sui tool, checkpoint di approvazione, limiti di budget, audit trail delle azioni, meccanismi di interruzione/rollback. Il Live Activity Monitor del progetto copre la parte di visibilità; l'enforcement (già escluso per la parte token, per scelta) resta demandato agli hook/permission nativi.

## 5. Deployment graduale, non big-bang

Percorso consigliato per introdurre controlli su un ambiente Claude Code: pilota su repo a basso rischio → permessi gestiti → sandboxing di Bash/devcontainer → restrizione MCP → hook → export telemetria → test avversariali sulla policy reale. Utile come riferimento per come proporre all'utente finale l'attivazione progressiva di un profilo/recipe, invece di un cambio di configurazione tutto-o-niente.

## 6. I controlli nativi non bastano da soli

Le capacità agentiche di Claude Code introducono rischi che i controlli nativi non coprono del tutto: servono difese a strati aggiuntive esterne (least-privilege, secret management, dependency scanning) — il control plane resta un livello di *orchestrazione/visibilità*, non sostituisce queste pratiche.

## Fonti

- [Claude Code Security: 6 Risks, Controls & Best Practices — Checkmarx](https://checkmarx.com/learn/ai-security/claude-code-security-top-6-risks-controls-and-best-practices/)
- [awesome-claude-code-security](https://github.com/efij/awesome-claude-code-security)
- [Anthropic Claude Code Security Best Practices — General Analysis](https://generalanalysis.com/guides/anthropic-claude-code-security-best-practices)
- [Claude Code settings — documentazione ufficiale](https://code.claude.com/docs/en/settings)
- [Where Is Claude Code settings.json? 5 Config Files, 1 Priority Rule](https://blog.vincentqiao.com/en/posts/claude-code-settings-intro/)
- [Global permissions overridden by project-level settings — issue #45639](https://github.com/anthropics/claude-code/issues/45639)
- [What Is an AI Agent Control Plane? — Guild.ai](https://www.guild.ai/blog/product/what-is-an-ai-agent-control-plane)
- [Control Plane for AI Agents: Connect, Secure, Observe, Govern](https://medium.com/@bijit211987/control-plane-for-ai-agents-connect-secure-observe-govern-0d9c1ea940ac)
