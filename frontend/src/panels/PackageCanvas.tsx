import { addEdge, applyEdgeChanges, applyNodeChanges } from '@xyflow/react'
import type { Connection, Edge, EdgeChange, NodeChange } from '@xyflow/react'
import { useCallback, useState } from 'react'
import {
  useActivatePackage,
  useCreatePackage,
  useDeactivatePackage,
  usePackages,
  usePreviewActivation,
  type PackageNodeIn,
  type PackageScope,
  type PackageSummary,
} from '../api/packages'
import { AddNodeForm } from '../canvas/AddNodeForm'
import { Canvas } from '../canvas/Canvas'
import type { PackageFlowNode, PackageNodeData } from '../canvas/Canvas'
import { ProjectSelector } from '../components/ProjectSelector'
import { useNavigationStore } from '../store/navigationStore'

function nodeDataToPackageNode(data: PackageNodeData): PackageNodeIn {
  return {
    type: data.nodeType,
    name: data.name,
    library_item_id: data.libraryItemId ?? null,
    config: data.config ?? null,
    content: data.content ?? null,
  }
}

function isFlowNodeArray(value: unknown): value is PackageFlowNode[] {
  return Array.isArray(value)
}

function isEdgeArray(value: unknown): value is Edge[] {
  return Array.isArray(value)
}

export function PackageCanvas() {
  const selectedProjectPath = useNavigationStore((state) => state.selectedProjectPath)
  const [nodes, setNodes] = useState<PackageFlowNode[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [packageId, setPackageId] = useState('')
  const [packageName, setPackageName] = useState('')
  const [version, setVersion] = useState('1.0.0')
  const [description, setDescription] = useState('')
  const [previewingId, setPreviewingId] = useState<string | null>(null)

  const scope: PackageScope = selectedProjectPath ? 'project' : 'global'

  const { data: packages } = usePackages()
  const createPackage = useCreatePackage()
  const activatePackage = useActivatePackage()
  const deactivatePackage = useDeactivatePackage()
  const { data: previewDiffs } = usePreviewActivation(previewingId)

  const handleNodesChange = useCallback((changes: NodeChange<PackageFlowNode>[]) => {
    setNodes((current) => applyNodeChanges(changes, current))
  }, [])

  const handleEdgesChange = useCallback((changes: EdgeChange[]) => {
    setEdges((current) => applyEdgeChanges(changes, current))
  }, [])

  const handleConnect = useCallback((connection: Connection) => {
    setEdges((current) => addEdge(connection, current))
  }, [])

  function handleAddNode(data: PackageNodeData) {
    setNodes((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        type: 'packageNode',
        position: { x: 80, y: 80 + current.length * 90 },
        data,
      },
    ])
  }

  function handleSave(e: React.FormEvent) {
    e.preventDefault()
    if (!packageId.trim() || !packageName.trim()) return
    createPackage.mutate({
      id: packageId.trim(),
      name: packageName.trim(),
      version,
      scope,
      project_path: selectedProjectPath,
      description,
      nodes: nodes.map((n) => nodeDataToPackageNode(n.data)),
      canvas_layout: { nodes, edges },
    })
  }

  function handleLoad(pkg: PackageSummary) {
    setPackageId(pkg.id)
    setPackageName(pkg.name)
    setVersion(pkg.version)
    setDescription(pkg.description)
    const layoutNodes = pkg.canvas_layout.nodes
    const layoutEdges = pkg.canvas_layout.edges
    setNodes(isFlowNodeArray(layoutNodes) ? layoutNodes : [])
    setEdges(isEdgeArray(layoutEdges) ? layoutEdges : [])
  }

  return (
    <div className="panel">
      <header className="panel-header">
        <h2>Canvas Pacchetti</h2>
        <ProjectSelector />
      </header>

      <div className="canvas-toolbar">
        <form className="package-meta-form" onSubmit={handleSave}>
          <input
            placeholder="id pacchetto"
            value={packageId}
            onChange={(e) => setPackageId(e.target.value)}
          />
          <input
            placeholder="nome"
            value={packageName}
            onChange={(e) => setPackageName(e.target.value)}
          />
          <input
            placeholder="versione"
            value={version}
            onChange={(e) => setVersion(e.target.value)}
          />
          <input
            placeholder="descrizione"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <span className="scope-badge">{scope}</span>
          <button type="submit" disabled={createPackage.isPending}>
            Salva come pacchetto
          </button>
        </form>

        <AddNodeForm onAdd={handleAddNode} />

        <select
          aria-label="Carica pacchetto esistente"
          value=""
          onChange={(e) => {
            const pkg = packages?.find((p) => p.id === e.target.value)
            if (pkg) handleLoad(pkg)
          }}
        >
          <option value="">Carica pacchetto…</option>
          {(packages ?? []).map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} ({p.scope})
            </option>
          ))}
        </select>
      </div>

      <Canvas
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={handleConnect}
      />

      {packages && packages.length > 0 && (
        <section className="package-activation-list">
          <h3>Pacchetti salvati</h3>
          <ul>
            {packages.map((p) => (
              <li key={p.id}>
                <strong>{p.name}</strong> ({p.scope})
                <button type="button" onClick={() => setPreviewingId(p.id)}>
                  Anteprima
                </button>
                <button
                  type="button"
                  onClick={() => activatePackage.mutate(p.id)}
                  disabled={activatePackage.isPending}
                >
                  Attiva
                </button>
                <button
                  type="button"
                  onClick={() => deactivatePackage.mutate(p.id)}
                  disabled={deactivatePackage.isPending}
                >
                  Disattiva
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {previewingId && previewDiffs && (
        <section className="activation-preview">
          <h3>Anteprima diff — {previewingId}</h3>
          <ul>
            {previewDiffs.map((d) => (
              <li key={d.relative_path} className={`diff-${d.action}`}>
                <code>{d.relative_path}</code> — {d.action}
              </li>
            ))}
          </ul>
          <button type="button" onClick={() => setPreviewingId(null)}>
            Chiudi
          </button>
        </section>
      )}

      {deactivatePackage.data && (
        <p className="hint">
          Rimossi: {deactivatePackage.data.removed.length} — Preservati (modificati manualmente):{' '}
          {deactivatePackage.data.preserved.length}
        </p>
      )}

      {createPackage.isError && (
        <p role="alert">Impossibile salvare il pacchetto: {createPackage.error.message}</p>
      )}
      {activatePackage.isError && (
        <p role="alert">Impossibile attivare il pacchetto: {activatePackage.error.message}</p>
      )}
      {deactivatePackage.isError && (
        <p role="alert">Impossibile disattivare il pacchetto: {deactivatePackage.error.message}</p>
      )}
    </div>
  )
}
