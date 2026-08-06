import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost } from './client'
import type { ProjectEntry } from './types'

const PROJECTS_QUERY_KEY = ['projects'] as const

export function useProjects() {
  return useQuery({
    queryKey: PROJECTS_QUERY_KEY,
    queryFn: () => apiGet<ProjectEntry[]>('/projects'),
  })
}

export function useRegisterProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (path: string) => apiPost<ProjectEntry>('/projects', { path }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY })
    },
  })
}
