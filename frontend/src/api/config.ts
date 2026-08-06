import { useQuery } from '@tanstack/react-query'
import { apiGet } from './client'
import type { GlobalConfig, ProjectConfig } from './types'

export function useGlobalConfig() {
  return useQuery({
    queryKey: ['config', 'global'],
    queryFn: () => apiGet<GlobalConfig>('/config/global'),
  })
}

export function useProjectConfig(projectPath: string | null) {
  return useQuery({
    queryKey: ['config', 'project', projectPath],
    queryFn: () =>
      apiGet<ProjectConfig>(`/config/project?path=${encodeURIComponent(projectPath!)}`),
    enabled: projectPath !== null,
  })
}
