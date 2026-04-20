import type { QueryClient } from '@tanstack/react-query'

/** Canonical first segment of query keys (use consistently across the app). */
export const QK = {
  cases: 'cases',
  case: 'case',
  machines: 'machines',
  controlSystems: 'control-systems',
  postVersions: 'post-versions',
  severities: 'severities',
  priorities: 'priorities',
  statuses: 'statuses',
  categories: 'categories',
  users: 'users',
  assignees: 'assignees',
  roles: 'roles',
  changeRequests: 'change-requests',
  testCases: 'test-cases',
  knowledge: 'knowledge',
  regressionRuns: 'regression-runs',
  systemBuilds: 'system-builds',
  dashProd: 'dash',
  dashEng: 'dash',
  dashAdm: 'dash',
} as const

export function invalidatePrefixes(qc: QueryClient, prefixes: readonly (readonly unknown[])[]): void {
  for (const prefix of prefixes) {
    void qc.invalidateQueries({ queryKey: [...prefix] as unknown[] })
  }
}

export function invalidateDashboards(qc: QueryClient): void {
  void qc.invalidateQueries({ queryKey: ['dash', 'prod'] })
  void qc.invalidateQueries({ queryKey: ['dash', 'eng'] })
  void qc.invalidateQueries({ queryKey: ['dash', 'adm'] })
}

/** After any case-scoped change: lists + detail + relations + dashboards. */
export function invalidateCaseEcosystem(qc: QueryClient, caseId: number): void {
  invalidatePrefixes(qc, [
    ['cases'],
    ['case', caseId],
    ['case', caseId, 'comments'],
    ['case', caseId, 'attachments'],
    ['case', caseId, 'rc'],
    ['case', caseId, 'rel'],
    ['case', caseId, 'hist'],
    ['change-requests'],
    ['test-cases'],
  ])
  invalidateDashboards(qc)
}

/** Related lists when a CRUD resource changes (beyond the entity's own list). */
export function relatedKeysForResource(resourceBase: string): readonly (readonly unknown[])[] {
  switch (resourceBase) {
    case '/api/v1/users':
      return [['assignees']]
    case '/api/v1/machines':
      return [['cases'], ['machines']]
    case '/api/v1/control-systems':
      return [['control-systems'], ['machines'], ['cases']]
    case '/api/v1/post-versions':
      return [['post-versions'], ['cases']]
    case '/api/v1/categories':
      return [['categories'], ['knowledge']]
    case '/api/v1/statuses':
      return [['statuses'], ['cases']]
    case '/api/v1/change-requests':
      return [['change-requests'], ['cases'], ['case']]
    case '/api/v1/test-cases':
      return [['test-cases'], ['cases'], ['case']]
    case '/api/v1/knowledge':
      return [['knowledge']]
    case '/api/v1/regression-runs':
      return [['regression-runs'], ['cases'], ['case']]
    case '/api/v1/cam-step-models':
      return [['cam-step-models'], ['cases'], ['case']]
    case '/api/v1/machine-post-bindings':
      return [['machine-post-bindings'], ['cases'], ['case']]
    case '/api/v1/system-builds':
      return [['system-builds']]
    default:
      return []
  }
}

export function invalidateAfterEntityWrite(
  qc: QueryClient,
  resourceBase: string,
  ownListQueryKey: readonly unknown[]
): void {
  invalidatePrefixes(qc, [ownListQueryKey, ...relatedKeysForResource(resourceBase)])
  invalidateDashboards(qc)
}
