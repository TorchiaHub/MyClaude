import { useState } from 'react'
import {
  useCheckpoints,
  useMemory,
  useOutputStyles,
  useRules,
  useSandboxConfig,
} from '../api/filesystem'
import { ProjectSelector } from '../components/ProjectSelector'
import { useNavigationStore } from '../store/navigationStore'

type SubTab = 'memory' | 'rules' | 'checkpoints' | 'sandbox' | 'output-styles'

const SUB_TABS: { key: SubTab; label: string }[] = [
  { key: 'memory', label: 'Auto Memory' },
  { key: 'rules', label: 'Rules Inspector' },
  { key: 'checkpoints', label: 'Checkpoint Viewer' },
  { key: 'sandbox', label: 'Sandboxing' },
  { key: 'output-styles', label: 'Output Styles' },
]

function formatTimestamp(epochSeconds: number): string {
  return new Date(epochSeconds * 1000).toLocaleString('it-IT')
}

function MemoryView({ projectPath }: { projectPath: string | null }) {
  const { data, isLoading, error } = useMemory(projectPath)

  if (!projectPath) return <p className="hint">Seleziona un progetto per vedere la sua memoria.</p>
  if (isLoading) return <p>Caricamento…</p>
  if (error) return <p className="empty">Nessuna auto memory trovata per questo progetto</p>
  if (!data) return null

  return (
    <div>
      <h3>Indice</h3>
      <pre className="memory-index">{data.index_content}</pre>
      <h3>Note tematiche</h3>
      {data.topics.length === 0 && <p className="empty">Nessuna nota</p>}
      <ul className="memory-topics">
        {data.topics.map((topic) => (
          <li key={topic.filename} className="memory-topic">
            <div className="memory-topic-header">
              <strong>{topic.name}</strong>
              <span className="hint">{formatTimestamp(topic.modified)}</span>
            </div>
            <p className="description">{topic.description}</p>
            <p>{topic.content}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}

function RulesView({ projectPath }: { projectPath: string | null }) {
  const { data, isLoading, error } = useRules(projectPath)

  if (isLoading) return <p>Caricamento…</p>
  if (error) return <p role="alert">Errore nel caricamento delle regole.</p>
  if (!data || data.length === 0) return <p className="empty">Nessuna regola trovata</p>

  return (
    <table className="mcp-servers-table">
      <thead>
        <tr>
          <th>Nome</th>
          <th>Scope</th>
          <th>Cartella</th>
          <th>Pattern</th>
        </tr>
      </thead>
      <tbody>
        {data.map((rule) => (
          <tr key={rule.file_path}>
            <td>{rule.name}</td>
            <td>{rule.scope}</td>
            <td>{rule.relative_folder || '—'}</td>
            <td>
              {rule.paths.map((p) => (
                <code key={p} className="rule-pattern">
                  {p}
                </code>
              ))}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function CheckpointsView({ projectPath }: { projectPath: string | null }) {
  const [sessionId, setSessionId] = useState('')
  const { data, isLoading, error } = useCheckpoints(sessionId || null, projectPath)

  return (
    <div>
      <label>
        Session ID
        <input
          placeholder="uuid sessione"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
        />
      </label>

      {!projectPath && <p className="hint">Seleziona anche un progetto.</p>}
      {isLoading && <p>Caricamento…</p>}
      {error && <p role="alert">Errore nel caricamento dei checkpoint.</p>}

      {data && (
        <>
          <p className="checkpoint-caveat" role="alert">
            {data.coverage_caveat}
          </p>
          {data.checkpoints.length === 0 && <p className="empty">Nessun checkpoint trovato</p>}
          <ul className="checkpoint-list">
            {data.checkpoints.map((cp) => (
              <li key={cp.message_id} className="checkpoint-item">
                <span className="hint">{cp.timestamp}</span>
                {cp.changed_files.length === 0 ? (
                  <span className="empty"> — nessun file tracciato</span>
                ) : (
                  <ul>
                    {cp.changed_files.map((f, i) => (
                      <li key={`${f}-${i}`}>
                        <code>{f}</code>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

function SandboxView() {
  const { data, isLoading, error } = useSandboxConfig()

  if (isLoading) return <p>Caricamento…</p>
  if (error) return <p role="alert">Errore nel caricamento della configurazione sandbox.</p>
  if (!data) return null

  return (
    <div>
      <p>
        Stato:{' '}
        <span className={data.enabled ? 'status-ok' : 'status-idle'}>
          {data.enabled ? 'configurato' : 'non configurato'}
        </span>
      </p>
      {data.auto_allow_bash_if_sandboxed !== null && (
        <p className="hint">
          autoAllowBashIfSandboxed: {String(data.auto_allow_bash_if_sandboxed)}
        </p>
      )}
      {data.enabled ? (
        <pre className="memory-index">{JSON.stringify(data.raw_config, null, 2)}</pre>
      ) : (
        <p className="empty">Nessuna configurazione sandbox attiva</p>
      )}
    </div>
  )
}

function OutputStylesView({ projectPath }: { projectPath: string | null }) {
  const { data, isLoading, error } = useOutputStyles(projectPath)

  if (isLoading) return <p>Caricamento…</p>
  if (error) return <p role="alert">Errore nel caricamento degli output style.</p>
  if (!data || data.length === 0) return <p className="empty">Nessun output style trovato</p>

  return (
    <ul className="library-items">
      {data.map((style) => (
        <li key={style.id} className="library-item">
          <div className="library-item-header">
            <span className="resource-type">{style.scope}</span>
            <strong>{style.name}</strong>
          </div>
          <p className="description">{style.description}</p>
        </li>
      ))}
    </ul>
  )
}

export function FilesystemExtensions() {
  const selectedProjectPath = useNavigationStore((state) => state.selectedProjectPath)
  const [subTab, setSubTab] = useState<SubTab>('memory')

  return (
    <div className="panel">
      <header className="panel-header">
        <h2>Estensioni Filesystem</h2>
        <ProjectSelector />
      </header>

      <div className="sub-tabs">
        {SUB_TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={tab.key === subTab ? 'active' : ''}
            onClick={() => setSubTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {subTab === 'memory' && <MemoryView projectPath={selectedProjectPath} />}
      {subTab === 'rules' && <RulesView projectPath={selectedProjectPath} />}
      {subTab === 'checkpoints' && <CheckpointsView projectPath={selectedProjectPath} />}
      {subTab === 'sandbox' && <SandboxView />}
      {subTab === 'output-styles' && <OutputStylesView projectPath={selectedProjectPath} />}
    </div>
  )
}
