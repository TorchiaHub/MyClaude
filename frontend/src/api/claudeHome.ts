import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiDelete, apiGet, apiPatch } from './client'

export interface ClaudeHomeFileEntry {
  name: string
  is_dir: boolean
  size: number
}

export interface ClaudeHomeGraphNode {
  id: string
  type: string
  label: string
}

export interface ClaudeHomeGraphEdge {
  source: string
  target: string
  kind: string
}

export interface ClaudeHomeGraph {
  nodes: ClaudeHomeGraphNode[]
  edges: ClaudeHomeGraphEdge[]
}

const TREE_KEY = ['claude-home', 'tree'] as const

export function useClaudeHomeGraph() {
  return useQuery({
    queryKey: ['claude-home', 'graph'],
    queryFn: () => apiGet<ClaudeHomeGraph>('/claude-home/graph'),
  })
}

export function useClaudeHomeTree(path: string) {
  return useQuery({
    queryKey: [...TREE_KEY, path],
    queryFn: () =>
      apiGet<ClaudeHomeFileEntry[]>(`/claude-home/tree?path=${encodeURIComponent(path)}`),
  })
}

export function useClaudeHomeFile(path: string | null) {
  return useQuery({
    queryKey: ['claude-home', 'file', path],
    queryFn: () =>
      apiGet<{ content: string }>(`/claude-home/file?path=${encodeURIComponent(path!)}`),
    enabled: path !== null,
  })
}

export function useRenameEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { path: string; new_name: string }) =>
      apiPatch<{ path: string }>('/claude-home/rename', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TREE_KEY })
    },
  })
}

export function useMoveEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { path: string; new_path: string }) =>
      apiPatch<{ path: string }>('/claude-home/move', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TREE_KEY })
    },
  })
}

export function useDeleteEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (path: string) => apiDelete(`/claude-home/entry?path=${encodeURIComponent(path)}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TREE_KEY })
    },
  })
}
