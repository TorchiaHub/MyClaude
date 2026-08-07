import type { Node } from '@xyflow/react'
import type { PackageNodeType } from '../api/packages'

export interface PackageNodeData extends Record<string, unknown> {
  nodeType: PackageNodeType
  name: string
  libraryItemId?: string
  config?: Record<string, unknown>
  content?: string
}

export type PackageFlowNode = Node<PackageNodeData>

export const NODE_TYPE_LABELS: Record<PackageNodeType, string> = {
  skill: 'Skill',
  agent: 'Agente',
  command: 'Comando',
  mcp: 'MCP',
  rule: 'Regola',
  prompt: 'Prompt',
}

export const NODE_TYPE_COLOR_VAR: Record<PackageNodeType, string> = {
  skill: '--series-1',
  agent: '--series-2',
  command: '--series-3',
  mcp: '--series-4',
  rule: '--series-5',
  prompt: '--series-6',
}
