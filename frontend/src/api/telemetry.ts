import { useQuery } from '@tanstack/react-query'
import { apiGet } from './client'
import type { TelemetrySummary } from './types'

export function useTelemetrySummary(
  projectPath: string | null,
  period?: { since?: string; until?: string },
) {
  return useQuery({
    queryKey: ['telemetry', 'summary', projectPath, period?.since, period?.until],
    queryFn: () => {
      const params = new URLSearchParams({ project_path: projectPath! })
      if (period?.since) params.set('since', period.since)
      if (period?.until) params.set('until', period.until)
      return apiGet<TelemetrySummary>(`/telemetry/summary?${params.toString()}`)
    },
    enabled: projectPath !== null,
  })
}
