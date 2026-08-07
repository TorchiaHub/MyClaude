import { useState } from 'react'
import { ActivityMonitor } from './panels/ActivityMonitor'
import { Comparator } from './panels/Comparator'
import { ConfigurationManager } from './panels/ConfigurationManager'
import { Dashboard } from './panels/Dashboard'
import { FilesystemExtensions } from './panels/FilesystemExtensions'
import { ImportExport } from './panels/ImportExport'
import { Library } from './panels/Library'
import { McpHub } from './panels/McpHub'
import { PackageCanvas } from './panels/PackageCanvas'
import { useNavigationStore, type PanelKey } from './store/navigationStore'
import './App.css'

const PANELS: { key: PanelKey; label: string }[] = [
  { key: 'config', label: 'Configuration Manager' },
  { key: 'mcp', label: 'MCP Hub' },
  { key: 'library', label: 'Library' },
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'canvas', label: 'Canvas Pacchetti' },
  { key: 'activity', label: 'Live Activity Monitor' },
  { key: 'comparator', label: 'Comparator' },
  { key: 'filesystem', label: 'Estensioni Filesystem' },
  { key: 'import-export', label: 'Import / Export' },
]

function ActivePanel({ panel }: { panel: PanelKey }) {
  switch (panel) {
    case 'config':
      return <ConfigurationManager />
    case 'mcp':
      return <McpHub />
    case 'library':
      return <Library />
    case 'dashboard':
      return <Dashboard />
    case 'canvas':
      return <PackageCanvas />
    case 'activity':
      return <ActivityMonitor />
    case 'comparator':
      return <Comparator />
    case 'filesystem':
      return <FilesystemExtensions />
    case 'import-export':
      return <ImportExport />
  }
}

function ShutdownButton() {
  const [status, setStatus] = useState<'idle' | 'shutting-down' | 'error'>('idle')

  async function handleShutdown() {
    try {
      const response = await fetch('/system/shutdown', { method: 'POST' })
      setStatus(response.ok ? 'shutting-down' : 'error')
    } catch {
      setStatus('error')
    }
  }

  return (
    <div className="shutdown-control">
      <button type="button" onClick={handleShutdown} disabled={status === 'shutting-down'}>
        {status === 'shutting-down' ? 'Arresto in corso…' : 'Spegni'}
      </button>
      {status === 'error' && <p role="alert">Impossibile contattare il backend.</p>}
    </div>
  )
}

function App() {
  const activePanel = useNavigationStore((state) => state.activePanel)
  const setActivePanel = useNavigationStore((state) => state.setActivePanel)

  return (
    <div className="app-shell">
      <nav className="app-nav">
        <h1>Control Plane</h1>
        <ul>
          {PANELS.map((panel) => (
            <li key={panel.key}>
              <button
                type="button"
                className={panel.key === activePanel ? 'active' : ''}
                onClick={() => setActivePanel(panel.key)}
              >
                {panel.label}
              </button>
            </li>
          ))}
        </ul>
        <ShutdownButton />
      </nav>
      <main className="app-content">
        <ActivePanel panel={activePanel} />
      </main>
    </div>
  )
}

export default App
