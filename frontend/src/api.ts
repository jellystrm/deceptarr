export interface SourceHit {
  url: string
  server?: string
  name?: string
}

export interface SourceResult {
  status: 'ok' | 'error'
  message?: string
  url?: string
  urls?: SourceHit[]
  episodes?: { num: number; url: string | null }[]
  found?: number
  total?: number
  log?: string[]
}

export interface SourceTestRequest {
  tmdb_id?: number
  media_type: 'movie' | 'tv'
  title?: string
  year?: number
  season?: number
  episode?: number
  tvdb_id?: number
}

export async function getConfig(): Promise<Record<string, unknown>> {
  const r = await fetch('/api/config')
  return r.json()
}

export async function getJobs(): Promise<{ jobs: unknown[] }> {
  const r = await fetch('/api/jobs')
  return r.json()
}

export async function sourceTest(
  payload: SourceTestRequest,
): Promise<Record<string, SourceResult>> {
  const r = await fetch('/api/source-test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return r.json()
}

export async function torznabSearch(params: URLSearchParams): Promise<string> {
  const r = await fetch('/torznab/api?' + params.toString())
  return r.text()
}
