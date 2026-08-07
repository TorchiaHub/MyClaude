import {
  Background,
  Controls,
  ReactFlow,
  ReactFlowProvider,
  type Connection,
  type Edge,
  type EdgeChange,
  type NodeChange,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useMemo } from 'react'
import { PackageNodeCard } from './PackageNodeCard'
import type { PackageFlowNode, PackageNodeData } from './types'

interface CanvasProps {
  nodes: PackageFlowNode[]
  edges: Edge[]
  onNodesChange: (changes: NodeChange<PackageFlowNode>[]) => void
  onEdgesChange: (changes: EdgeChange[]) => void
  onConnect: (connection: Connection) => void
}

function CanvasInner({ nodes, edges, onNodesChange, onEdgesChange, onConnect }: CanvasProps) {
  const nodeTypes = useMemo(() => ({ packageNode: PackageNodeCard }), [])

  return (
    <div className="canvas-container">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  )
}

export function Canvas(props: CanvasProps) {
  return (
    <ReactFlowProvider>
      <CanvasInner {...props} />
    </ReactFlowProvider>
  )
}

export type { PackageFlowNode, PackageNodeData }
