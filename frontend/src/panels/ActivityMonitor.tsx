import { useState } from 'react'
import { useLiveActivity, useSessionDrilldown } from '../api/activity'

function statusClass(status: string): string {
  return status === 'busy' ? 'status-busy' : 'status-idle'
}

function SessionDrilldown({ sessionId, cwd }: { sessionId: string; cwd: string }) {
  const { data: events, isLoading } = useSessionDrilldown(sessionId, cwd)

  if (isLoading) return <p>Caricamento…</p>
  if (!events || events.length === 0) {
    return <p className="empty">Nessuna attività registrata</p>
  }

  const recentEvents = events.slice(-5).reverse()

  return (
    <ul className="drilldown-events">
      {recentEvents.map((event, index) => (
        <li key={`${event.timestamp}-${index}`}>
          <code>{event.tool_name}</code>
          <span className="hint">{event.timestamp}</span>
        </li>
      ))}
    </ul>
  )
}

export function ActivityMonitor() {
  const { sessions, connected } = useLiveActivity()
  const [expandedSessionId, setExpandedSessionId] = useState<string | null>(null)

  function toggleSession(sessionId: string) {
    setExpandedSessionId((current) => (current === sessionId ? null : sessionId))
  }

  return (
    <div className="panel">
      <header className="panel-header">
        <h2>Live Activity Monitor</h2>
        <span className={connected ? 'status-ok' : 'status-error'}>
          {connected ? 'connesso' : 'disconnesso'}
        </span>
      </header>

      {sessions.length === 0 && <p className="empty">Nessuna sessione attiva</p>}

      <ul className="session-list">
        {sessions.map((session) => (
          <li key={session.session_id} className="session-item">
            <button
              type="button"
              className="session-summary"
              onClick={() => toggleSession(session.session_id)}
            >
              <span className={statusClass(session.status)}>{session.status}</span>
              <strong>{session.name ?? session.session_id.slice(0, 8)}</strong>
              <span className="hint">{session.cwd}</span>
              <span className="hint">pid {session.pid}</span>
            </button>
            {expandedSessionId === session.session_id && (
              <SessionDrilldown sessionId={session.session_id} cwd={session.cwd} />
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
