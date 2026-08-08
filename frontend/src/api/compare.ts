import { useQuery } from '@tanstack/react-query'
import { apiGet } from './client'

export interface NodeTypeDiff {
  only_in_a: string[]
  only_in_b: string[]
  common: string[]
}

export interface StaticDiff {
  package_a_id: string
  package_b_id: string
  is_identical: boolean
  by_type: Record<string, NodeTypeDiff>
}

export interface TelemetrySlice {
  turn_count: number
  period_input_tokens: number
  period_output_tokens: number
  tokens_by_model: Record<string, { input_tokens: number; output_tokens: number }>
}

export interface IsolatedSummary extends TelemetrySlice {
  package_id: string
  windows: [number, number | null][]
}

export interface CompareStaticResult {
  static_diff: StaticDiff
}

export interface CompareIsolatedResult extends CompareStaticResult {
  isolated: { a: IsolatedSummary; b: IsolatedSummary }
}

export interface CompareCombinationResult {
  combination: {
    a: { active_package_ids: string[]; telemetry: TelemetrySlice }
    b: { active_package_ids: string[]; telemetry: TelemetrySlice }
  }
}

interface CompareParamsBase {
  a: string
  b: string
}

interface StaticParams extends CompareParamsBase {
  mode: 'static'
}

interface IsolatedParams extends CompareParamsBase {
  mode: 'isolated'
  projectPath: string
  since?: string
  until?: string
}

interface CombinationParams {
  mode: 'combination'
  projectPath: string
  sinceA: string
  untilA: string
  sinceB: string
  untilB: string
}

type CompareParams = StaticParams | IsolatedParams | CombinationParams

function buildQuery(params: CompareParams): URLSearchParams {
  const query = new URLSearchParams({ mode: params.mode })

  if (params.mode === 'static' || params.mode === 'isolated') {
    query.set('a', params.a)
    query.set('b', params.b)
  }
  if (params.mode === 'isolated') {
    query.set('project_path', params.projectPath)
    if (params.since) query.set('since', params.since)
    if (params.until) query.set('until', params.until)
  }
  if (params.mode === 'combination') {
    query.set('project_path', params.projectPath)
    query.set('since_a', params.sinceA)
    query.set('until_a', params.untilA)
    query.set('since_b', params.sinceB)
    query.set('until_b', params.untilB)
  }
  return query
}

export function useCompare(params: CompareParams | null) {
  return useQuery({
    queryKey: ['packages', 'compare', params],
    queryFn: () =>
      apiGet<CompareStaticResult | CompareIsolatedResult | CompareCombinationResult>(
        `/packages/compare?${buildQuery(params!).toString()}`,
      ),
    enabled: params !== null,
  })
}
