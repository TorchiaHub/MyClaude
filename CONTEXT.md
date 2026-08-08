# Claude Code Control Plane

Web app locale per gestire, configurare e osservare visivamente l'ambiente Claude Code sulla macchina dell'utente.

## Language

**Pacchetto**:
Unità riusabile composta su canvas (skill + agenti + MCP + regole + prompt), scope `global` o `project`, schema in DESIGN.md §5.
_Avoid_: Recipe — usato per errore in IMPLEMENTATION_PLAN.md (tabella rischi), termine da correggere lì, non da propagare.

**Import pull**:
Il Control Plane *legge* un progetto esistente e cataloga file non ancora coperti (CLAUDE.md, hook, altri tipi) come risorse sfogliabili — nessuna scrittura sul progetto sorgente.
_Avoid_: "Import automatico" da solo, senza specificare la direzione — ambiguo tra pull e push.

**Import push**:
L'attivazione di un pacchetto scrive anche questi tipi di file (CLAUDE.md, hook, ecc.) nel progetto target, oltre a skill/agenti/comandi/MCP/regole già coperti da `activation_engine`. Richiede la stessa validazione server-side già usata per skill/agenti/comandi (`library_item_id` risolto contro il catalogo locale, mai un path libero dal client).
_Avoid_: Confonderlo con l'`activation_engine` esistente, che oggi copre solo skill/agenti/comandi/MCP/regole/prompt — il push per CLAUDE.md/hook/altri tipi è un'estensione dello schema pacchetto, non ancora costruita.
