import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPut } from './client'
import type { EffectivePermissions, GlobalConfig, ProjectConfig } from './types'

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

export function useUpdateGlobalPermissions() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (rules: EffectivePermissions) =>
      apiPut<{ effective_permissions: EffectivePermissions }>('/config/global/permissions', rules),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config', 'global'] })
    },
  })
}

export function useUpdateProjectPermissions(projectPath: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (rules: EffectivePermissions) =>
      apiPut<{ own_permissions: EffectivePermissions }>(
        `/config/project/permissions?path=${encodeURIComponent(projectPath!)}`,
        rules,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config', 'project', projectPath] })
    },
  })
}
