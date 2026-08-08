import { useQuery } from '@tanstack/react-query'
import { apiGet } from './client'

export interface MemoryTopic {
  filename: string
  name: string
  description: string
  metadata: Record<string, unknown>
  content: string
  modified: number
}

export interface ProjectMemory {
  index_content: string
  topics: MemoryTopic[]
}

export function useMemory(projectPath: string | null) {
  return useQuery({
    queryKey: ['memory', projectPath],
    queryFn: () =>
      apiGet<ProjectMemory>(`/memory?project_path=${encodeURIComponent(projectPath!)}`),
    enabled: projectPath !== null,
    retry: false,
  })
}

export interface RuleInfo {
  name: string
  scope: 'user' | 'project'
  relative_folder: string
  paths: string[]
  file_path: string
}

export function useRules(projectPath: string | null) {
  return useQuery({
    queryKey: ['rules', projectPath],
    queryFn: () =>
      apiGet<RuleInfo[]>(
        projectPath ? `/rules?project_path=${encodeURIComponent(projectPath)}` : '/rules',
      ),
  })
}

export interface Checkpoint {
  message_id: string
  timestamp: string
  changed_files: string[]
}

export interface CheckpointTimeline {
  checkpoints: Checkpoint[]
  coverage_caveat: string
}

export function useCheckpoints(sessionId: string | null, cwd: string | null) {
  return useQuery({
    queryKey: ['checkpoints', sessionId, cwd],
    queryFn: () =>
      apiGet<CheckpointTimeline>(
        `/checkpoints/${encodeURIComponent(sessionId!)}?cwd=${encodeURIComponent(cwd!)}`,
      ),
    enabled: sessionId !== null && cwd !== null,
  })
}

export interface SandboxConfig {
  enabled: boolean
  raw_config: Record<string, unknown>
  auto_allow_bash_if_sandboxed: boolean | null
}

export function useSandboxConfig() {
  return useQuery({
    queryKey: ['sandbox', 'config'],
    queryFn: () => apiGet<SandboxConfig>('/sandbox/config'),
  })
}

export interface OutputStyleInfo {
  id: string
  scope: 'user' | 'project'
  name: string
  description: string
  path: string
}

export function useOutputStyles(projectPath: string | null) {
  return useQuery({
    queryKey: ['output-styles', projectPath],
    queryFn: () =>
      apiGet<OutputStyleInfo[]>(
        projectPath
          ? `/output-styles?project_path=${encodeURIComponent(projectPath)}`
          : '/output-styles',
      ),
  })
}
