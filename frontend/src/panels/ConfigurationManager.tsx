import { useGlobalConfig, useProjectConfig } from '../api/config'
import { ProjectSelector } from '../components/ProjectSelector'
import { useNavigationStore } from '../store/navigationStore'
import type { EffectivePermissions } from '../api/types'

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

function GlobalConfigView() {
  const { data, isLoading, error } = useGlobalConfig()

  if (isLoading) return <p>Caricamento configurazione globale…</p>
  if (error) return <p role="alert">Errore nel caricamento della configurazione globale.</p>
  if (!data) return null

  return (
    <section>
      <h3>Configurazione globale</h3>
      <p className="hint">
        Vista di sola lettura. La scrittura sicura (merge/append con anteprima diff) sarà
        disponibile nel pannello di attivazione pacchetti.
      </p>
      <EffectivePermissionsView permissions={data.effective_permissions} />
    </section>
  )
}

function ProjectConfigView({ projectPath }: { projectPath: string }) {
  const { data, isLoading, error } = useProjectConfig(projectPath)

  if (isLoading) return <p>Caricamento configurazione progetto…</p>
  if (error) return <p role="alert">Errore nel caricamento della configurazione del progetto.</p>
  if (!data) return null

  return (
    <section>
      <h3>Configurazione progetto</h3>
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
