import { useState } from 'react'
import { useTelemetrySummary } from '../api/telemetry'
import { ProjectSelector } from '../components/ProjectSelector'
import { useNavigationStore } from '../store/navigationStore'

const MODEL_COLOR_SLOTS = ['--series-1', '--series-2', '--series-3', '--series-4'] as const

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-tile">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
    </div>
  )
}

function formatUsd(value: number): string {
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'USD' }).format(value)
}

function formatTokens(value: number): string {
  return new Intl.NumberFormat('it-IT').format(value)
}

function TokensByModelChart({
  tokensByModel,
}: {
  tokensByModel: Record<string, { input_tokens: number; output_tokens: number }>
}) {
  const entries = Object.entries(tokensByModel)
  if (entries.length === 0) {
    return <p className="empty">Nessun token registrato nel periodo selezionato</p>
  }

  const totals = entries.map(([model, t]) => ({
    model,
    total: t.input_tokens + t.output_tokens,
  }))
  const maxTotal = Math.max(...totals.map((t) => t.total), 1)

  return (
    <div className="tokens-chart">
      <svg viewBox={`0 0 640 ${entries.length * 28}`} role="img" aria-label="Token per modello">
        {totals.map(({ model, total }, i) => {
          const width = (total / maxTotal) * 200
          const color = `var(${MODEL_COLOR_SLOTS[i % MODEL_COLOR_SLOTS.length]})`
          return (
            <g key={model} transform={`translate(0, ${i * 28})`}>
              <rect x={0} y={4} width={width} height={16} rx={4} fill={color}>
                <title>{`${model}: ${formatTokens(total)} token`}</title>
              </rect>
              <text x={width + 8} y={16} className="chart-label">
                {model}
              </text>
            </g>
          )
        })}
      </svg>
      <table className="tokens-table">
        <caption className="visually-hidden">Token per modello, vista tabellare</caption>
        <thead>
          <tr>
            <th>Modello</th>
            <th>Input</th>
            <th>Output</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([model, t]) => (
            <tr key={model}>
              <td>{model}</td>
              <td>{formatTokens(t.input_tokens)}</td>
              <td>{formatTokens(t.output_tokens)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Dashboard() {
  const selectedProjectPath = useNavigationStore((state) => state.selectedProjectPath)
  const [since, setSince] = useState('')
  const [until, setUntil] = useState('')
  const { data, isLoading, error } = useTelemetrySummary(selectedProjectPath, {
    since: since ? `${since}T00:00:00Z` : undefined,
    until: until ? `${until}T23:59:59Z` : undefined,
  })

  return (
    <div className="panel">
      <header className="panel-header">
        <h2>Token & Cost Dashboard</h2>
        <ProjectSelector />
      </header>

      {!selectedProjectPath && <p className="hint">Seleziona un progetto per vedere i dati.</p>}

      {selectedProjectPath && (
        <>
          <div className="period-filter">
            <label>
              Da
              <input type="date" value={since} onChange={(e) => setSince(e.target.value)} />
            </label>
            <label>
              A
              <input type="date" value={until} onChange={(e) => setUntil(e.target.value)} />
            </label>
          </div>

          {isLoading && <p>Caricamento telemetria…</p>}
          {error && <p role="alert">Errore nel caricamento della telemetria.</p>}

          {data && (
            <>
              <div className="stat-tiles">
                <StatTile
                  label="Costo cumulativo"
                  value={data.cumulative ? formatUsd(data.cumulative.cost_usd) : '—'}
                />
                <StatTile label="Turni nel periodo" value={String(data.turn_count)} />
                <StatTile
                  label="Token input (periodo)"
                  value={formatTokens(data.period_input_tokens)}
                />
                <StatTile
                  label="Token output (periodo)"
                  value={formatTokens(data.period_output_tokens)}
                />
              </div>

              <h3>Breakdown per modello (periodo)</h3>
              <TokensByModelChart tokensByModel={data.tokens_by_model} />
            </>
          )}
        </>
      )}
    </div>
  )
}
