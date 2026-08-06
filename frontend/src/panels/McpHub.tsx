import { useState } from 'react'
import { useAddMcpServer, useMcpServers, useRemoveMcpServer, useTestMcpServer } from '../api/mcp'
import { ProjectSelector } from '../components/ProjectSelector'
import { useNavigationStore } from '../store/navigationStore'

function AddServerForm({ projectPath }: { projectPath: string | null }) {
  const [name, setName] = useState('')
  const [command, setCommand] = useState('')
  const addServer = useAddMcpServer(projectPath)
  const scope = projectPath ? 'project' : 'global'

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !command.trim()) return
    addServer.mutate(
      { name: name.trim(), scope, projectPath, config: { command: command.trim() } },
      {
        onSuccess: () => {
          setName('')
          setCommand('')
        },
      },
    )
  }

  return (
    <form className="add-server-form" onSubmit={handleSubmit}>
      <input
        placeholder="nome server"
        value={name}
        onChange={(e) => setName(e.target.value)}
        aria-label="Nome server MCP"
      />
      <input
        placeholder="comando stdio"
        value={command}
        onChange={(e) => setCommand(e.target.value)}
        aria-label="Comando"
      />
      <button type="submit" disabled={addServer.isPending}>
        Aggiungi ({scope})
      </button>
      {addServer.isError && <p role="alert">Impossibile aggiungere il server.</p>}
    </form>
  )
}

function TestServerButton({
  name,
  scope,
  projectPath,
}: {
  name: string
  scope: 'global' | 'project'
  projectPath: string | null
}) {
  const testServer = useTestMcpServer()

  return (
    <>
      <button
        type="button"
        onClick={() => testServer.mutate({ name, scope, projectPath })}
        disabled={testServer.isPending}
      >
        Test
      </button>
      {testServer.data && (
        <span className={testServer.data.reachable ? 'status-ok' : 'status-error'}>
          {testServer.data.detail}
        </span>
      )}
    </>
  )
}

export function McpHub() {
  const selectedProjectPath = useNavigationStore((state) => state.selectedProjectPath)
  const { data: servers, isLoading, error } = useMcpServers(selectedProjectPath)
  const removeServer = useRemoveMcpServer(selectedProjectPath)

  return (
    <div className="panel">
      <header className="panel-header">
        <h2>MCP Hub</h2>
        <ProjectSelector />
      </header>

      <AddServerForm projectPath={selectedProjectPath} />

      {isLoading && <p>Caricamento server MCP…</p>}
      {error && <p role="alert">Errore nel caricamento dei server MCP.</p>}

      {servers && servers.length === 0 && <p className="empty">Nessun server MCP configurato</p>}

      {servers && servers.length > 0 && (
        <table className="mcp-servers-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Scope</th>
              <th>Comando/URL</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {servers.map((server) => (
              <tr key={`${server.scope}:${server.name}`}>
                <td>{server.name}</td>
                <td>{server.scope}</td>
                <td>
                  <code>{server.config.command ?? server.config.url}</code>
                </td>
                <td>
                  <TestServerButton
                    name={server.name}
                    scope={server.scope}
                    projectPath={selectedProjectPath}
                  />
                  <button
                    type="button"
                    onClick={() =>
                      removeServer.mutate({
                        name: server.name,
                        scope: server.scope,
                        projectPath: selectedProjectPath,
                      })
                    }
                    disabled={removeServer.isPending}
                  >
                    Rimuovi
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
