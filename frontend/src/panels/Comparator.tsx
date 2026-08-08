import { useState } from 'react'
import {
  useCompare,
  type CompareCombinationResult,
  type CompareIsolatedResult,
  type StaticDiff,
} from '../api/compare'
import {
  useInstallSessionStartHook,
  useSessionStartHookStatus,
  useUninstallSessionStartHook,
} from '../api/hooks'
import { usePackages } from '../api/packages'

type Mode = 'static' | 'isolated' | 'combination'

function SessionCorrelationStatus() {
  const { data: status, isLoading } = useSessionStartHookStatus()
  const install = useInstallSessionStartHook()
  const uninstall = useUninstallSessionStartHook()

  if (isLoading) return null

  return (
    <div className="hook-status">
      <span className={status?.installed ? 'status-ok' : 'status-idle'}>
        Correlazione sessione↔pacchetto: {status?.installed ? 'attiva' : 'non attiva'}
      </span>
      {status?.installed ? (
        <button type="button" onClick={() => uninstall.mutate()} disabled={uninstall.isPending}>
          Disattiva
        </button>
      ) : (
        <button type="button" onClick={() => install.mutate()} disabled={install.isPending}>
          Attiva (installa hook SessionStart)
        </button>
      )}
    </div>
  )
}

function PackageSelect({
  label,
  value,
  onChange,
  packageIds,
}: {
  label: string
  value: string
  onChange: (id: string) => void
  packageIds: string[]
}) {
  return (
    <label>
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">— scegli —</option>
        {packageIds.map((id) => (
          <option key={id} value={id}>
            {id}
          </option>
        ))}
      </select>
    </label>
  )
}

function StaticDiffView({ diff }: { diff: StaticDiff }) {
  const rows = Object.entries(diff.by_type).filter(
    ([, d]) => d.only_in_a.length > 0 || d.only_in_b.length > 0 || d.common.length > 0,
  )

  return (
    <section>
      <h3>Differenza di composizione</h3>
      {diff.is_identical && <p className="hint">I due pacchetti hanno la stessa composizione.</p>}
      {rows.length === 0 && !diff.is_identical && (
        <p className="empty">Nessun nodo in nessuno dei due pacchetti</p>
      )}
      {rows.length > 0 && (
        <table className="mcp-servers-table">
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Solo in A</th>
              <th>Solo in B</th>
              <th>In comune</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([type, d]) => (
              <tr key={type}>
                <td>{type}</td>
                <td>{d.only_in_a.join(', ') || '—'}</td>
                <td>{d.only_in_b.join(', ') || '—'}</td>
                <td>{d.common.join(', ') || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

function IsolatedView({ result }: { result: CompareIsolatedResult }) {
  return (
    <section>
      <h3>Contributo isolato (storico)</h3>
      <table className="mcp-servers-table">
        <thead>
          <tr>
            <th>Pacchetto</th>
            <th>Finestre attive</th>
            <th>Turni</th>
            <th>Token input</th>
            <th>Token output</th>
          </tr>
        </thead>
        <tbody>
          {[result.isolated.a, result.isolated.b].map((summary) => (
            <tr key={summary.package_id}>
              <td>{summary.package_id}</td>
              <td>{summary.windows.length}</td>
              <td>{summary.turn_count}</td>
              <td>{summary.period_input_tokens}</td>
              <td>{summary.period_output_tokens}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function CombinationView({ result }: { result: CompareCombinationResult }) {
  return (
    <section>
      <h3>Combinazione attiva nel tempo (storico)</h3>
      <table className="mcp-servers-table">
        <thead>
          <tr>
            <th>Periodo</th>
            <th>Pacchetti attivi</th>
            <th>Turni</th>
            <th>Token input</th>
            <th>Token output</th>
          </tr>
        </thead>
        <tbody>
          {(['a', 'b'] as const).map((key) => {
            const period = result.combination[key]
            return (
              <tr key={key}>
                <td>Periodo {key.toUpperCase()}</td>
                <td>{period.active_package_ids.join(', ') || '—'}</td>
                <td>{period.telemetry.turn_count}</td>
                <td>{period.telemetry.period_input_tokens}</td>
                <td>{period.telemetry.period_output_tokens}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </section>
  )
}

export function Comparator() {
  const { data: packages } = usePackages()
  const [mode, setMode] = useState<Mode>('static')
  const [packageA, setPackageA] = useState('')
  const [packageB, setPackageB] = useState('')
  const [projectPath, setProjectPath] = useState('')
  const [since, setSince] = useState('')
  const [until, setUntil] = useState('')
  const [sinceA, setSinceA] = useState('')
  const [untilA, setUntilA] = useState('')
  const [sinceB, setSinceB] = useState('')
  const [untilB, setUntilB] = useState('')

  const packageIds = (packages ?? []).map((p) => p.id)

  const canQuery =
    mode === 'static'
      ? packageA !== '' && packageB !== ''
      : mode === 'isolated'
        ? packageA !== '' && packageB !== '' && projectPath !== ''
        : projectPath !== '' && sinceA !== '' && untilA !== '' && sinceB !== '' && untilB !== ''

  const params = !canQuery
    ? null
    : mode === 'static'
      ? ({ mode: 'static', a: packageA, b: packageB } as const)
      : mode === 'isolated'
        ? ({
            mode: 'isolated',
            a: packageA,
            b: packageB,
            projectPath,
            since: since ? `${since}T00:00:00Z` : undefined,
            until: until ? `${until}T23:59:59Z` : undefined,
          } as const)
        : ({
            mode: 'combination',
            projectPath,
            sinceA: `${sinceA}T00:00:00Z`,
            untilA: `${untilA}T23:59:59Z`,
            sinceB: `${sinceB}T00:00:00Z`,
            untilB: `${untilB}T23:59:59Z`,
          } as const)

  const { data, isLoading, error } = useCompare(params)

  return (
    <div className="panel">
      <header className="panel-header">
        <h2>Workflow Comparator</h2>
        <SessionCorrelationStatus />
      </header>

      <div className="comparator-controls">
        <label>
          Modalità
          <select value={mode} onChange={(e) => setMode(e.target.value as Mode)}>
            <option value="static">Diff statico</option>
            <option value="isolated">Pacchetto isolato (storico)</option>
            <option value="combination">Combinazione nel tempo (storico)</option>
          </select>
        </label>

        {(mode === 'static' || mode === 'isolated') && (
          <>
            <PackageSelect
              label="Pacchetto A"
              value={packageA}
              onChange={setPackageA}
              packageIds={packageIds}
            />
            <PackageSelect
              label="Pacchetto B"
              value={packageB}
              onChange={setPackageB}
              packageIds={packageIds}
            />
          </>
        )}

        {(mode === 'isolated' || mode === 'combination') && (
          <label>
            Progetto (path assoluto)
            <input
              placeholder="/home/utente/progetto"
              value={projectPath}
              onChange={(e) => setProjectPath(e.target.value)}
            />
          </label>
        )}

        {mode === 'isolated' && (
          <>
            <label>
              Da (opzionale)
              <input type="date" value={since} onChange={(e) => setSince(e.target.value)} />
            </label>
            <label>
              A (opzionale)
              <input type="date" value={until} onChange={(e) => setUntil(e.target.value)} />
            </label>
          </>
        )}

        {mode === 'combination' && (
          <>
            <label>
              Periodo A — da
              <input type="date" value={sinceA} onChange={(e) => setSinceA(e.target.value)} />
            </label>
            <label>
              a
              <input type="date" value={untilA} onChange={(e) => setUntilA(e.target.value)} />
            </label>
            <label>
              Periodo B — da
              <input type="date" value={sinceB} onChange={(e) => setSinceB(e.target.value)} />
            </label>
            <label>
              a
              <input type="date" value={untilB} onChange={(e) => setUntilB(e.target.value)} />
            </label>
          </>
        )}
      </div>

      {!canQuery && <p className="hint">Compila i campi per vedere il confronto.</p>}
      {isLoading && <p>Caricamento confronto…</p>}
      {error && <p role="alert">Errore nel calcolo del confronto.</p>}

      {data && 'static_diff' in data && <StaticDiffView diff={data.static_diff} />}
      {data && 'isolated' in data && <IsolatedView result={data} />}
      {data && 'combination' in data && <CombinationView result={data} />}
    </div>
  )
}
