import { Background, Controls, Handle, Position, ReactFlow, ReactFlowProvider } from '@xyflow/react'
import type { Edge, Node, NodeProps } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useMemo, useState } from 'react'
import {
  useClaudeHomeFile,
  useClaudeHomeGraph,
  useClaudeHomeTree,
  useDeleteEntry,
  useMoveEntry,
  useRenameEntry,
} from '../api/claudeHome'

type SubTab = 'canvas' | 'folders'

const NODE_TYPE_ORDER = [
  'memory',
  'settings',
  'skill',
  'agent',
  'command',
  'output_style',
  'rule',
  'script',
]

const NODE_TYPE_LABELS: Record<string, string> = {
  memory: 'CLAUDE.md',
  settings: 'Settings',
  skill: 'Skill',
  agent: 'Agente',
  command: 'Comando',
  output_style: 'Output Style',
  rule: 'Regola',
  script: 'Script',
}

const COLUMN_WIDTH = 220
const ROW_HEIGHT = 70

interface ClaudeHomeNodeData extends Record<string, unknown> {
  label: string
  nodeType: string
}

function ClaudeHomeNodeCard({ data }: NodeProps<Node<ClaudeHomeNodeData>>) {
  return (
    <div className="package-node-card">
      <Handle type="target" position={Position.Left} />
      <span className="package-node-type">{NODE_TYPE_LABELS[data.nodeType] ?? data.nodeType}</span>
      <strong className="package-node-name">{data.label}</strong>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

function ClaudeHomeCanvas() {
  const { data, isLoading, error } = useClaudeHomeGraph()
  const nodeTypes = useMemo(() => ({ claudeHomeNode: ClaudeHomeNodeCard }), [])

  if (isLoading) return <p>Caricamento…</p>
  if (error) return <p role="alert">Errore nel caricamento del grafo.</p>
  if (!data) return null

  const connectedIds = new Set<string>()
  for (const edge of data.edges) {
    connectedIds.add(edge.source)
    connectedIds.add(edge.target)
  }
  const anchorTypes = new Set(['memory', 'settings'])
  const visibleNodes = data.nodes.filter(
    (node) => connectedIds.has(node.id) || anchorTypes.has(node.type),
  )

  const nodesByType = new Map<string, typeof data.nodes>()
  for (const node of visibleNodes) {
    const list = nodesByType.get(node.type) ?? []
    list.push(node)
    nodesByType.set(node.type, list)
  }

  const flowNodes: Node<ClaudeHomeNodeData>[] = []
  NODE_TYPE_ORDER.forEach((type, columnIndex) => {
    const items = nodesByType.get(type) ?? []
    items.forEach((node, rowIndex) => {
      flowNodes.push({
        id: node.id,
        type: 'claudeHomeNode',
        position: { x: columnIndex * COLUMN_WIDTH, y: rowIndex * ROW_HEIGHT },
        data: { label: node.label, nodeType: node.type },
      })
    })
  })

  const flowEdges: Edge[] = data.edges.map((edge, index) => ({
    id: `${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    label: edge.kind,
  }))

  return (
    <div>
      <p className="hint">
        {visibleNodes.length} nodi collegati su {data.nodes.length} totali — il catalogo completo è
        nella tab "Cartelle" o nel pannello Library.
      </p>
      <div className="canvas-container">
        <ReactFlowProvider>
          <ReactFlow
            nodes={flowNodes}
            edges={flowEdges}
            nodeTypes={nodeTypes}
            nodesDraggable={false}
            nodesConnectable={false}
            fitView
          >
            <Background />
            <Controls />
          </ReactFlow>
        </ReactFlowProvider>
      </div>
    </div>
  )
}

function TreeBranch({
  path,
  depth,
  selectedFile,
  onSelectFile,
}: {
  path: string
  depth: number
  selectedFile: string | null
  onSelectFile: (path: string) => void
}) {
  const { data: entries, isLoading } = useClaudeHomeTree(path)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [renamingPath, setRenamingPath] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [movingPath, setMovingPath] = useState<string | null>(null)
  const [moveValue, setMoveValue] = useState('')
  const renameEntry = useRenameEntry()
  const moveEntry = useMoveEntry()
  const deleteEntry = useDeleteEntry()

  if (isLoading) return <p className="hint">Caricamento…</p>
  if (!entries) return null

  function childPath(name: string): string {
    return path ? `${path}/${name}` : name
  }

  function toggle(fullPath: string) {
    setExpanded((current) => {
      const next = new Set(current)
      if (next.has(fullPath)) next.delete(fullPath)
      else next.add(fullPath)
      return next
    })
  }

  function handleRenameSubmit(e: React.FormEvent, fullPath: string) {
    e.preventDefault()
    if (renameValue.trim()) renameEntry.mutate({ path: fullPath, new_name: renameValue.trim() })
    setRenamingPath(null)
  }

  function handleMoveSubmit(e: React.FormEvent, fullPath: string) {
    e.preventDefault()
    if (moveValue.trim()) moveEntry.mutate({ path: fullPath, new_path: moveValue.trim() })
    setMovingPath(null)
  }

  function handleDelete(fullPath: string) {
    const confirmed = window.confirm(
      `Eliminare definitivamente "${fullPath}"? L'azione non è reversibile.`,
    )
    if (confirmed) deleteEntry.mutate(fullPath)
  }

  return (
    <ul className="claude-home-tree">
      {entries.map((entry) => {
        const fullPath = childPath(entry.name)
        const isExpanded = expanded.has(fullPath)
        return (
          <li key={fullPath} className="claude-home-tree-entry">
            <div className="claude-home-tree-row">
              {entry.is_dir ? (
                <button type="button" onClick={() => toggle(fullPath)}>
                  {isExpanded ? '▾' : '▸'} {entry.name}
                </button>
              ) : (
                <button
                  type="button"
                  className={selectedFile === fullPath ? 'active' : ''}
                  onClick={() => onSelectFile(fullPath)}
                >
                  {entry.name}
                </button>
              )}
              <span className="claude-home-tree-actions">
                <button
                  type="button"
                  onClick={() => {
                    setRenamingPath(fullPath)
                    setRenameValue(entry.name)
                  }}
                >
                  Rinomina
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMovingPath(fullPath)
                    setMoveValue(fullPath)
                  }}
                >
                  Sposta
                </button>
                <button type="button" onClick={() => handleDelete(fullPath)}>
                  Elimina
                </button>
              </span>
            </div>

            {renamingPath === fullPath && (
              <form
                className="permission-add-form"
                onSubmit={(e) => handleRenameSubmit(e, fullPath)}
              >
                <input value={renameValue} onChange={(e) => setRenameValue(e.target.value)} />
                <button type="submit">Conferma</button>
                <button type="button" onClick={() => setRenamingPath(null)}>
                  Annulla
                </button>
              </form>
            )}

            {movingPath === fullPath && (
              <form className="permission-add-form" onSubmit={(e) => handleMoveSubmit(e, fullPath)}>
                <input value={moveValue} onChange={(e) => setMoveValue(e.target.value)} />
                <button type="submit">Conferma</button>
                <button type="button" onClick={() => setMovingPath(null)}>
                  Annulla
                </button>
              </form>
            )}

            {entry.is_dir && isExpanded && (
              <TreeBranch
                path={fullPath}
                depth={depth + 1}
                selectedFile={selectedFile}
                onSelectFile={onSelectFile}
              />
            )}
          </li>
        )
      })}
    </ul>
  )
}

function FolderTreeView() {
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const { data: fileData, isLoading: isFileLoading } = useClaudeHomeFile(selectedFile)

  return (
    <div className="claude-home-browser">
      <div className="claude-home-tree-panel">
        <TreeBranch path="" depth={0} selectedFile={selectedFile} onSelectFile={setSelectedFile} />
      </div>
      <div className="claude-home-preview-panel">
        {selectedFile ? (
          <>
            <h4>{selectedFile}</h4>
            {isFileLoading ? (
              <p>Caricamento…</p>
            ) : (
              <pre className="memory-index">{fileData?.content}</pre>
            )}
          </>
        ) : (
          <p className="hint">Seleziona un file per vedere l'anteprima.</p>
        )}
      </div>
    </div>
  )
}

export function ClaudeGlobal() {
  const [subTab, setSubTab] = useState<SubTab>('canvas')

  return (
    <div className="panel">
      <header className="panel-header">
        <h2>Claude Globale</h2>
      </header>
      <p className="hint">
        Mappa e navigazione dell'intero ambiente globale di Claude Code (~/.claude/) — inclusi file
        operativi e di sessione. Rinomina/sposta/elimina agiscono direttamente sul filesystem reale,
        senza conferma per rinomina/sposta e con conferma solo per l'eliminazione.
      </p>
      <div className="sub-tabs">
        <button
          type="button"
          className={subTab === 'canvas' ? 'active' : ''}
          onClick={() => setSubTab('canvas')}
        >
          Canvas
        </button>
        <button
          type="button"
          className={subTab === 'folders' ? 'active' : ''}
          onClick={() => setSubTab('folders')}
        >
          Cartelle
        </button>
      </div>
      {subTab === 'canvas' && <ClaudeHomeCanvas />}
      {subTab === 'folders' && <FolderTreeView />}
    </div>
  )
}
