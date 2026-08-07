import { useState } from 'react'
import {
  useGlobalConfig,
  useProjectConfig,
  useUpdateGlobalPermissions,
  useUpdateProjectPermissions,
} from '../api/config'
import { ProjectSelector } from '../components/ProjectSelector'
import { useNavigationStore } from '../store/navigationStore'
import type { EffectivePermissions } from '../api/types'

type RuleType = keyof EffectivePermissions

const RULE_TYPES: RuleType[] = ['allow', 'ask', 'deny']
const RULE_TYPE_LABELS: Record<RuleType, string> = { allow: 'Allow', ask: 'Ask', deny: 'Deny' }

function movePermissionRule(
  permissions: EffectivePermissions,
  rule: string,
  from: RuleType,
  to: RuleType,
): EffectivePermissions {
  if (from === to) return permissions
  return {
    ...permissions,
    [from]: permissions[from].filter((r) => r !== rule),
    [to]: permissions[to].includes(rule) ? permissions[to] : [...permissions[to], rule],
  }
}

function removePermissionRule(
  permissions: EffectivePermissions,
  rule: string,
  from: RuleType,
): EffectivePermissions {
  return { ...permissions, [from]: permissions[from].filter((r) => r !== rule) }
}

function addPermissionRule(
  permissions: EffectivePermissions,
  rule: string,
  to: RuleType,
): EffectivePermissions {
  const trimmed = rule.trim()
  const alreadyPresent = RULE_TYPES.some((type) => permissions[type].includes(trimmed))
  if (!trimmed || alreadyPresent) return permissions
  return { ...permissions, [to]: [...permissions[to], trimmed] }
}

function PermissionList({ title, rules }: { title: string; rules: string[] }) {
  return (
    <div className="permission-list">
      <h4>{title}</h4>
      {rules.length === 0 ? (
        <p className="empty">Nessuna regola</p>
      ) : (
        <ul>
          {rules.map((rule) => (
            <li key={rule}>
              <code>{rule}</code>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function EffectivePermissionsView({ permissions }: { permissions: EffectivePermissions }) {
  return (
    <div className="effective-permissions">
      <PermissionList title="Allow" rules={permissions.allow} />
      <PermissionList title="Ask" rules={permissions.ask} />
      <PermissionList title="Deny" rules={permissions.deny} />
    </div>
  )
}

function EditablePermissionList({
  ruleType,
  permissions,
  onChange,
  disabled,
}: {
  ruleType: RuleType
  permissions: EffectivePermissions
  onChange: (next: EffectivePermissions) => void
  disabled: boolean
}) {
  const [newRule, setNewRule] = useState('')
  const otherTypes = RULE_TYPES.filter((t) => t !== ruleType)
  const rules = permissions[ruleType]

  function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    onChange(addPermissionRule(permissions, newRule, ruleType))
    setNewRule('')
  }

  return (
    <div className="permission-list">
      <h4>{RULE_TYPE_LABELS[ruleType]}</h4>
      {rules.length === 0 ? (
        <p className="empty">Nessuna regola</p>
      ) : (
        <ul>
          {rules.map((rule) => (
            <li key={rule} className="permission-rule">
              <code>{rule}</code>
              <span className="permission-rule-actions">
                {otherTypes.map((target) => (
                  <button
                    key={target}
                    type="button"
                    disabled={disabled}
                    onClick={() =>
                      onChange(movePermissionRule(permissions, rule, ruleType, target))
                    }
                  >
                    → {RULE_TYPE_LABELS[target]}
                  </button>
                ))}
                <button
                  type="button"
                  disabled={disabled}
                  aria-label={`Rimuovi ${rule}`}
                  onClick={() => onChange(removePermissionRule(permissions, rule, ruleType))}
                >
                  ×
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
      <form className="permission-add-form" onSubmit={handleAdd}>
        <input
          placeholder="nuova regola"
          value={newRule}
          disabled={disabled}
          onChange={(e) => setNewRule(e.target.value)}
        />
        <button type="submit" disabled={disabled}>
          +
        </button>
      </form>
    </div>
  )
}

function EditableEffectivePermissionsView({
  permissions,
  onChange,
  disabled,
}: {
  permissions: EffectivePermissions
  onChange: (next: EffectivePermissions) => void
  disabled: boolean
}) {
  return (
    <div className="effective-permissions">
      {RULE_TYPES.map((ruleType) => (
        <EditablePermissionList
          key={ruleType}
          ruleType={ruleType}
          permissions={permissions}
          onChange={onChange}
          disabled={disabled}
        />
      ))}
    </div>
  )
}

function GlobalConfigView() {
  const { data, isLoading, error } = useGlobalConfig()
  const updatePermissions = useUpdateGlobalPermissions()

  if (isLoading) return <p>Caricamento configurazione globale…</p>
  if (error) return <p role="alert">Errore nel caricamento della configurazione globale.</p>
  if (!data) return null

  return (
    <section>
      <h3>Configurazione globale</h3>
      <p className="hint">
        Scrive direttamente su ~/.claude/settings.json — si applica a tutte le sessioni Claude Code
        su questa macchina.
      </p>
      <EditableEffectivePermissionsView
        permissions={data.effective_permissions}
        onChange={(next) => updatePermissions.mutate(next)}
        disabled={updatePermissions.isPending}
      />
      {updatePermissions.isError && (
        <p role="alert">Impossibile salvare: {updatePermissions.error.message}</p>
      )}
    </section>
  )
}

function ProjectConfigView({ projectPath }: { projectPath: string }) {
  const { data, isLoading, error } = useProjectConfig(projectPath)
  const updatePermissions = useUpdateProjectPermissions(projectPath)

  if (isLoading) return <p>Caricamento configurazione progetto…</p>
  if (error) return <p role="alert">Errore nel caricamento della configurazione del progetto.</p>
  if (!data) return null

  return (
    <section>
      <h3>Configurazione progetto</h3>
      <p className="hint">
        Regole proprie di questo progetto (.claude/settings.json) — modificabili qui sotto. La vista
        "effettiva" mostra anche il contributo di globale e locale (settings.local.json sovrascrive
        per tipo se presente, non modificabile da qui).
      </p>
      <EditableEffectivePermissionsView
        permissions={data.own_permissions}
        onChange={(next) => updatePermissions.mutate(next)}
        disabled={updatePermissions.isPending}
      />
      {updatePermissions.isError && (
        <p role="alert">Impossibile salvare: {updatePermissions.error.message}</p>
      )}
      <h4>Vista effettiva (sola lettura)</h4>
      <EffectivePermissionsView permissions={data.effective_permissions} />
      <h4>Server MCP di progetto</h4>
      {Object.keys(data.mcp_servers).length === 0 ? (
        <p className="empty">Nessun server MCP configurato per questo progetto</p>
      ) : (
        <ul>
          {Object.entries(data.mcp_servers).map(([name, config]) => (
            <li key={name}>
              <strong>{name}</strong> — <code>{config.command ?? config.url}</code>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export function ConfigurationManager() {
  const selectedProjectPath = useNavigationStore((state) => state.selectedProjectPath)

  return (
    <div className="panel">
      <header className="panel-header">
        <h2>Configuration Manager</h2>
        <ProjectSelector />
      </header>
      <GlobalConfigView />
      {selectedProjectPath && <ProjectConfigView projectPath={selectedProjectPath} />}
    </div>
  )
}
