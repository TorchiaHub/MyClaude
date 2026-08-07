import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost } from './client'
import type { CanvasLayout, PackageScope, PackageSummary } from './packages'

export interface ExportBundle {
  id: string
  name: string
  version: string
  scope: PackageScope
  description: string
  folder: string | null
  canvas_layout: CanvasLayout
  files: Record<string, string>
}

export interface MissingDependencies {
  missing_skills: string[]
  missing_agents: string[]
  missing_commands: string[]
  missing_mcp_servers: string[]
}

export interface ImportPackageInput {
  bundle: ExportBundle
  id: string
  scope: PackageScope
  project_path?: string | null
  folder?: string | null
}

export interface ImportPackageResult {
  package: PackageSummary
  missing_dependencies: MissingDependencies
}

export function useExportPackage() {
  return useMutation({
    mutationFn: (id: string) => apiGet<ExportBundle>(`/packages/${encodeURIComponent(id)}/export`),
  })
}

export function useImportPackage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: ImportPackageInput) =>
      apiPost<ImportPackageResult>('/packages/import', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['packages'] })
    },
  })
}
