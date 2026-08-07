import { Handle, Position, type NodeProps } from '@xyflow/react'
import { NODE_TYPE_COLOR_VAR, NODE_TYPE_LABELS, type PackageFlowNode } from './types'

export function PackageNodeCard({ data, selected }: NodeProps<PackageFlowNode>) {
  const colorVar = NODE_TYPE_COLOR_VAR[data.nodeType]

  return (
    <div
      className="package-node-card"
      style={{
        borderColor: selected ? `var(${colorVar})` : undefined,
      }}
    >
      <Handle type="target" position={Position.Top} />
      <span className="package-node-type" style={{ background: `var(${colorVar})` }}>
        {NODE_TYPE_LABELS[data.nodeType]}
      </span>
      <strong className="package-node-name">{data.name}</strong>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}
