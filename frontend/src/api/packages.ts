import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost, apiDelete } from './client'

export type PackageScope = 'global' | 'project'
export type PackageNodeType = 'skill' | 'agent' | 'command' | 'mcp' | 'rule' | 'prompt'

export interface PackageNodeIn {
  type: PackageNodeType
  name: string
  library_item_id?: string | null
  config?: Record<string, unknown> | null
  content?: string | null
}

export interface CanvasLayout {
  nodes: unknown[]
  edges: unknown[]
}

export interface PackageCreateInput {
  id: string
  name: string
  version: string
  scope: PackageScope
  project_path?: string | null
  folder?: string | null
  description?: string
  nodes: PackageNodeIn[]
  canvas_layout: CanvasLayout
}

export interface PackageSummary {
  id: string
  name: string
  version: string
  scope: PackageScope
  project_path: string | null
  content_path: string
  folder: string | null
  description: string
  updated_at: number
  canvas_layout: CanvasLayout
}

export interface FileDiff {
  relative_path: string
  action: 'create' | 'overwrite_identical' | 'overwrite_conflict'
}

export interface DeactivationResult {
  removed: string[]
  preserved: string[]
}

const PACKAGES_KEY = ['packages'] as const

export function usePackages() {
  return useQuery({
    queryKey: PACKAGES_KEY,
    queryFn: () => apiGet<PackageSummary[]>('/packages'),
  })
}

export function useCreatePackage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: PackageCreateInput) => apiPost<PackageSummary>('/packages', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PACKAGES_KEY })
    },
  })
}

export function useDeletePackage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiDelete(`/packages/${encodeURIComponent(id)}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PACKAGES_KEY })
    },
  })
}

export function usePreviewActivation(packageId: string | null) {
  return useQuery({
    queryKey: ['packages', packageId, 'preview'],
    queryFn: () =>
      apiGet<FileDiff[]>(`/packages/${encodeURIComponent(packageId!)}/preview-activation`),
    enabled: packageId !== null,
  })
}

export function useActivatePackage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiPost(`/packages/${encodeURIComponent(id)}/activate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PACKAGES_KEY })
    },
  })
}

export function useDeactivatePackage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      apiPost<DeactivationResult>(`/packages/${encodeURIComponent(id)}/deactivate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PACKAGES_KEY })
    },
  })
}
