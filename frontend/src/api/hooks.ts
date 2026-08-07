import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiDelete, apiGet, apiPost } from './client'

const HOOK_STATUS_KEY = ['hooks', 'session-start', 'status'] as const

export function useSessionStartHookStatus() {
  return useQuery({
    queryKey: HOOK_STATUS_KEY,
    queryFn: () => apiGet<{ installed: boolean }>('/hooks/session-start/status'),
  })
}

export function useInstallSessionStartHook() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => apiPost<{ installed: boolean }>('/hooks/session-start/install'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: HOOK_STATUS_KEY })
    },
  })
}

export function useUninstallSessionStartHook() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => apiDelete<{ uninstalled: boolean }>('/hooks/session-start/install'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: HOOK_STATUS_KEY })
    },
  })
}
