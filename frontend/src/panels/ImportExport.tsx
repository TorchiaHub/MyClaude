import { useState } from 'react'
import type { ExportBundle } from '../api/importExport'
import { useExportPackage, useImportPackage } from '../api/importExport'
import { usePackages, type PackageScope } from '../api/packages'
import { ProjectSelector } from '../components/ProjectSelector'
import { useNavigationStore } from '../store/navigationStore'

function downloadBundle(bundle: ExportBundle) {
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${bundle.id}.json`
  link.click()
  URL.revokeObjectURL(url)
}

function ExportSection() {
  const { data: packages } = usePackages()
  const exportPackage = useExportPackage()

  function handleExport(id: string) {
    exportPackage.mutate(id, { onSuccess: downloadBundle })
  }

  return (
    <section>
      <h3>Esporta</h3>
      {!packages || packages.length === 0 ? (
        <p className="empty">Nessun pacchetto da esportare</p>
      ) : (
        <ul className="library-items">
          {packages.map((p) => (
            <li key={p.id} className="library-item">
              <div className="library-item-header">
                <span className="resource-type">{p.scope}</span>
                <strong>{p.name}</strong>
                <button
                  type="button"
                  onClick={() => handleExport(p.id)}
                  disabled={exportPackage.isPending}
                >
                  Esporta (JSON sanitizzato)
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {exportPackage.isError && (
        <p role="alert">Impossibile esportare: {exportPackage.error.message}</p>
      )}
    </section>
  )
}

function ImportSection() {
  const selectedProjectPath = useNavigationStore((state) => state.selectedProjectPath)
  const [bundle, setBundle] = useState<ExportBundle | null>(null)
  const [parseError, setParseError] = useState<string | null>(null)
  const [id, setId] = useState('')
  const [folder, setFolder] = useState('')
  const importPackage = useImportPackage()

  const scope: PackageScope = selectedProjectPath ? 'project' : 'global'

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const parsed = JSON.parse(reader.result as string) as ExportBundle
        setBundle(parsed)
        setId(parsed.id)
        setFolder(parsed.folder ?? '')
        setParseError(null)
      } catch {
        setBundle(null)
        setParseError('Il file selezionato non è un JSON valido.')
      }
    }
    reader.readAsText(file)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!bundle || !id.trim()) return
    importPackage.mutate({
      bundle,
      id: id.trim(),
      scope,
      project_path: selectedProjectPath,
      folder: folder.trim() || null,
    })
  }

  return (
    <section>
      <h3>Importa</h3>
      <form className="package-meta-form" onSubmit={handleSubmit}>
        <input type="file" accept="application/json" onChange={handleFileChange} />
        <input placeholder="id pacchetto" value={id} onChange={(e) => setId(e.target.value)} />
        <input placeholder="cartella" value={folder} onChange={(e) => setFolder(e.target.value)} />
        <span className="scope-badge">{scope}</span>
        <button type="submit" disabled={!bundle || importPackage.isPending}>
          Importa
        </button>
      </form>

      {parseError && <p role="alert">{parseError}</p>}
      {importPackage.isError && <p role="alert">Import fallito: {importPackage.error.message}</p>}

      {importPackage.data && (
        <div className="hint">
          <p>Pacchetto importato: {importPackage.data.package.id}</p>
          <MissingDependenciesReport missing={importPackage.data.missing_dependencies} />
        </div>
      )}
    </section>
  )
}

function MissingDependenciesReport({
  missing,
}: {
  missing: {
    missing_skills: string[]
    missing_agents: string[]
    missing_commands: string[]
    missing_mcp_servers: string[]
  }
}) {
  const groups = [
    { label: 'Skill mancanti', items: missing.missing_skills },
    { label: 'Agenti mancanti', items: missing.missing_agents },
    { label: 'Comandi mancanti', items: missing.missing_commands },
    { label: 'Server MCP mancanti', items: missing.missing_mcp_servers },
  ].filter((g) => g.items.length > 0)

  if (groups.length === 0) {
    return (
      <p className="status-ok">Nessuna dipendenza mancante: tutte le risorse sono già locali.</p>
    )
  }

  return (
    <div role="alert">
      <p>Dipendenze non trovate localmente — mappale manualmente prima di attivare il pacchetto:</p>
      <ul>
        {groups.map((g) => (
          <li key={g.label}>
            {g.label}: {g.items.join(', ')}
          </li>
        ))}
      </ul>
    </div>
  )
}

export function ImportExport() {
  return (
    <div className="panel">
      <header className="panel-header">
        <h2>Import / Export</h2>
        <ProjectSelector />
      </header>
      <p className="hint">
        L'export rimuove automaticamente chiavi API e percorsi assoluti locali prima di produrre il
        file JSON.
      </p>
      <ExportSection />
      <ImportSection />
    </div>
  )
}
