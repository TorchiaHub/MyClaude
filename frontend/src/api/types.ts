export interface EffectivePermissions {
  allow: string[]
  ask: string[]
  deny: string[]
}

export interface GlobalConfig {
  claude_json: Record<string, unknown>
  settings: Record<string, unknown>
  effective_permissions: EffectivePermissions
}

export interface ProjectConfig {
  settings: Record<string, unknown>
  local_settings: Record<string, unknown>
  mcp_servers: Record<string, McpServerConfig>
  own_permissions: EffectivePermissions
  effective_permissions: EffectivePermissions
}

export interface McpServerConfig {
  type?: string
  command?: string
  args?: string[]
  url?: string
  env?: Record<string, string>
}

export interface McpServerEntry {
  name: string
  scope: 'global' | 'project'
  config: McpServerConfig
}

export type LibraryResourceType = 'skill' | 'agent' | 'command' | 'output_style'

export interface LibraryItem {
  id: string
  resource_type: LibraryResourceType
  scope: 'user' | 'project'
  name: string
  description: string
  folder: string
  path: string
  tags: string[]
  bookmarked: boolean
}

export interface ProjectEntry {
  path: string
  source: 'auto' | 'manual'
}

export interface ProjectCumulativeUsage {
  cost_usd: number
  total_input_tokens: number
  total_output_tokens: number
  total_cache_creation_input_tokens: number
  total_cache_read_input_tokens: number
  last_session_id: string | null
  model_usage: Record<string, Record<string, number>>
}

export interface TelemetrySummary {
  cumulative: ProjectCumulativeUsage | null
  turn_count: number
  period_input_tokens: number
  period_output_tokens: number
  tokens_by_model: Record<string, { input_tokens: number; output_tokens: number }>
}
