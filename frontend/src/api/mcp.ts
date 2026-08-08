import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiDelete, apiGet, apiPost } from './client'
import type { McpServerConfig, McpServerEntry } from './types'

function serversQueryKey(projectPath: string | null) {
  return ['mcp', 'servers', projectPath] as const
}

export function useMcpServers(projectPath: string | null) {
  return useQuery({
    queryKey: serversQueryKey(projectPath),
    queryFn: () =>
      apiGet<McpServerEntry[]>(
        projectPath
          ? `/mcp/servers?project_path=${encodeURIComponent(projectPath)}`
          : '/mcp/servers',
      ),
  })
}

interface AddServerInput {
  name: string
  scope: 'global' | 'project'
  projectPath: string | null
  config: McpServerConfig
}

export function useAddMcpServer(projectPath: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: AddServerInput) =>
      apiPost('/mcp/servers', {
        name: input.name,
        scope: input.scope,
        project_path: input.projectPath,
        config: input.config,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: serversQueryKey(projectPath) })
    },
  })
}

interface RemoveServerInput {
  name: string
  scope: 'global' | 'project'
  projectPath: string | null
}

export function useRemoveMcpServer(projectPath: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: RemoveServerInput) =>
      apiDelete(`/mcp/servers/${encodeURIComponent(input.name)}`, {
        scope: input.scope,
        project_path: input.projectPath,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: serversQueryKey(projectPath) })
    },
  })
}

interface TestServerInput {
  name: string
  scope: 'global' | 'project'
  projectPath: string | null
}

interface TestServerResult {
  reachable: boolean
  detail: string
}

export function useTestMcpServer() {
  return useMutation({
    mutationFn: (input: TestServerInput) =>
      apiPost<TestServerResult>(`/mcp/servers/${encodeURIComponent(input.name)}/test`, {
        scope: input.scope,
        project_path: input.projectPath,
      }),
  })
}
