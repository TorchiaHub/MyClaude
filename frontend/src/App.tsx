import { useState } from 'react'
import './App.css'

function App() {
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
    <main>
      <h1>Claude Code Control Plane</h1>
      <button type="button" onClick={handleShutdown} disabled={status === 'shutting-down'}>
        {status === 'shutting-down' ? 'Arresto in corso…' : 'Spegni'}
      </button>
      {status === 'error' && <p role="alert">Impossibile contattare il backend.</p>}
    </main>
  )
}

export default App
