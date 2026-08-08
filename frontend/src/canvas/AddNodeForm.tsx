import { useState } from 'react'
import { useLibrary } from '../api/library'
import { useMcpServers } from '../api/mcp'
import { NODE_TYPE_LABELS, type PackageNodeData } from './types'
import type { PackageNodeType } from '../api/packages'

interface AddNodeFormProps {
  onAdd: (data: PackageNodeData) => void
}

const LIBRARY_NODE_TYPES: PackageNodeType[] = ['skill', 'agent', 'command']

export function AddNodeForm({ onAdd }: AddNodeFormProps) {
  const [nodeType, setNodeType] = useState<PackageNodeType>('skill')
  const [selectedLibraryId, setSelectedLibraryId] = useState('')
  const [selectedMcpName, setSelectedMcpName] = useState('')
  const [ruleName, setRuleName] = useState('')
  const [ruleContent, setRuleContent] = useState('')

  const { data: libraryItems } = useLibrary(null)
  const { data: mcpServers } = useMcpServers(null)

  const isLibraryType = LIBRARY_NODE_TYPES.includes(nodeType)
  const filteredLibraryItems = (libraryItems ?? []).filter(
    (item) => item.resource_type === nodeType,
  )

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (isLibraryType) {
      const item = filteredLibraryItems.find((i) => i.id === selectedLibraryId)
      if (!item) return
      onAdd({
        nodeType,
        name: item.name,
        libraryItemId: item.id,
      })
      setSelectedLibraryId('')
      return
    }

    if (nodeType === 'mcp') {
      const server = (mcpServers ?? []).find((s) => s.name === selectedMcpName)
      if (!server) return
      onAdd({ nodeType, name: server.name, config: { ...server.config } })
      setSelectedMcpName('')
      return
    }

    if (!ruleName.trim()) return
    onAdd({ nodeType, name: ruleName.trim(), content: ruleContent })
    setRuleName('')
    setRuleContent('')
  }

  return (
    <form className="add-node-form" onSubmit={handleSubmit}>
      <select value={nodeType} onChange={(e) => setNodeType(e.target.value as PackageNodeType)}>
        {Object.entries(NODE_TYPE_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>

      {isLibraryType && (
        <select
          value={selectedLibraryId}
          onChange={(e) => setSelectedLibraryId(e.target.value)}
          aria-label={`Scegli ${NODE_TYPE_LABELS[nodeType]}`}
        >
          <option value="">— scegli —</option>
          {filteredLibraryItems.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
      )}

      {nodeType === 'mcp' && (
        <select
          value={selectedMcpName}
          onChange={(e) => setSelectedMcpName(e.target.value)}
          aria-label="Scegli server MCP"
        >
          <option value="">— scegli —</option>
          {(mcpServers ?? []).map((server) => (
            <option key={server.name} value={server.name}>
              {server.name}
            </option>
          ))}
        </select>
      )}

      {(nodeType === 'rule' || nodeType === 'prompt') && (
        <>
          <input
            placeholder="nome"
            value={ruleName}
            onChange={(e) => setRuleName(e.target.value)}
            aria-label="Nome"
          />
          <textarea
            placeholder="contenuto"
            value={ruleContent}
            onChange={(e) => setRuleContent(e.target.value)}
            aria-label="Contenuto"
            rows={2}
          />
        </>
      )}

      <button type="submit">Aggiungi nodo</button>
    </form>
  )
}
