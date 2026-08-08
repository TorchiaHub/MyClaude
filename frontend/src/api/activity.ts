import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { apiGet } from './client'

export interface SessionInfo {
  pid: number
  session_id: string
  cwd: string
  status: string
  name: string | null
  started_at: number | null
  updated_at: number | null
}

export function useLiveActivity() {
  const [sessions, setSessions] = useState<SessionInfo[]>([])
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const socket = new WebSocket(`${protocol}//${window.location.host}/activity/live`)

    socket.onopen = () => setConnected(true)
    socket.onclose = () => setConnected(false)
    socket.onmessage = (event) => {
      setSessions(JSON.parse(event.data) as SessionInfo[])
    }

    return () => socket.close()
  }, [])

  return { sessions, connected }
}

export interface ActivityEvent {
  timestamp: string
  tool_name: string
  session_id: string | null
}

export function useSessionDrilldown(sessionId: string | null, cwd: string | null) {
  return useQuery({
    queryKey: ['activity', 'drilldown', sessionId, cwd],
    queryFn: () =>
      apiGet<ActivityEvent[]>(
        `/activity/sessions/${encodeURIComponent(sessionId!)}/drilldown?cwd=${encodeURIComponent(cwd!)}`,
      ),
    enabled: sessionId !== null && cwd !== null,
  })
}
