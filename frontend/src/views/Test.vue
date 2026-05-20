<template>
  <div>
    <!-- Source Resolver -->
    <div class="card" style="margin-bottom: 16px">
      <div class="card-header">
        <div class="card-title">Source Resolver</div>
        <div class="card-desc">Test HLS URL resolution per-source — enter a TMDb ID and check which sources can serve it.</div>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="field">
            <label class="label">TMDb ID</label>
            <input v-model="sr.tmdbId" type="number" placeholder="27205 (Inception) / 1396 (Breaking Bad)" />
          </div>
          <div class="field">
            <label class="label">Title Override</label>
            <input v-model="sr.title" placeholder="Optional when TMDB key is empty" />
          </div>
          <div class="field">
            <label class="label">Year</label>
            <input v-model="sr.year" type="number" placeholder="2010" style="width:90px" />
          </div>
          <div class="field">
            <label class="label">Media Type</label>
            <select v-model="sr.mediaType">
              <option value="movie">Movie</option>
              <option value="tv">TV Series</option>
            </select>
          </div>
          <div v-if="sr.mediaType === 'tv'" class="row" style="gap:8px;flex-wrap:wrap;margin:0">
            <div class="field">
              <label class="label">Season</label>
              <input v-model="sr.season" type="number" min="1" placeholder="1" style="width:80px" />
            </div>
            <div class="field">
              <label class="label">Episode</label>
              <input v-model="sr.episode" type="number" min="1" placeholder="all" style="width:80px" />
            </div>
            <div class="field">
              <label class="label">TVDb ID</label>
              <input v-model="sr.tvdbId" type="number" placeholder="optional" style="width:110px" />
            </div>
          </div>
        </div>
        <div class="actions">
          <button class="btn" :disabled="sr.loading" @click="resolve">
            {{ sr.loading ? 'Resolving…' : '▶ Resolve' }}
          </button>
        </div>
        <div class="results">
          <p v-if="sr.loading" class="muted">{{ scanMsg }}…</p>
          <table v-else-if="sr.results" class="tbl">
            <tbody>
              <tr v-for="(r, name) in sr.results" :key="name">
                <td class="name">{{ name }}</td>
                <td><span :class="['dot', r.status === 'ok' ? 'ok' : 'err']" /></td>
                <td>
                  <template v-if="r.status === 'ok'">
                    <template v-if="r.episodes">
                      <div class="muted xs">Found {{ r.found }}/{{ r.total }} episodes</div>
                      <a
                        v-for="ep in r.episodes.filter(e => e.url)"
                        :key="ep.num"
                        :href="ep.url!"
                        target="_blank"
                        class="ep-link"
                      >E{{ String(ep.num).padStart(2, '0') }}</a>
                      <span v-if="!r.found" class="red xs">No episodes found</span>
                    </template>
                    <template v-else>
                      <div v-for="(u, i) in (r.urls || [{ url: r.url, server: '', name: '' }])" :key="i" class="url-row">
                        <span v-if="u.server || u.name" class="muted xs">{{ [u.server, u.name].filter(Boolean).join(' / ') }} </span>
                        <a :href="u.url" target="_blank" class="url-link">{{ i + 1 }}. {{ (u.url || '').slice(0, 120) }}{{ (u.url?.length ?? 0) > 120 ? '…' : '' }}</a>
                      </div>
                    </template>
                  </template>
                  <span v-else class="red xs">{{ r.message || 'Not found' }}</span>
                  <details v-if="r.log?.length" class="log-details">
                    <summary class="muted xs pointer">trace log</summary>
                    <div class="log-block">
                      <div v-for="(line, i) in r.log" :key="i">{{ line }}</div>
                    </div>
                  </details>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Torznab Tester -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">Torznab Query Tester</div>
        <div class="card-desc">Simulate the exact HTTP request Radarr/Sonarr sends — inspect titles and grab URLs.</div>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="field">
            <label class="label">API Key</label>
            <input v-model="tz.apiKey" />
          </div>
          <div class="field">
            <label class="label">Type (t=)</label>
            <select v-model="tz.type">
              <option value="movie">movie — Radarr</option>
              <option value="tvsearch">tvsearch — Sonarr</option>
            </select>
          </div>
        </div>
        <div v-if="tz.type === 'movie'" class="row">
          <div class="field"><label class="label">Title (q=)</label><input v-model="tz.q" placeholder="Inception" /></div>
          <div class="field"><label class="label">Year</label><input v-model="tz.year" type="number" placeholder="2010" /></div>
          <div class="field"><label class="label">TMDb ID</label><input v-model="tz.tmdbId" type="number" placeholder="27205" /></div>
          <div class="field"><label class="label">IMDb ID</label><input v-model="tz.imdbId" placeholder="tt1375666" /></div>
        </div>
        <div v-else class="row">
          <div class="field"><label class="label">Series Title (q=)</label><input v-model="tz.q" placeholder="Breaking Bad" /></div>
          <div class="field"><label class="label">TVDb ID</label><input v-model="tz.tvdbId" type="number" placeholder="81189" /></div>
          <div class="field"><label class="label">TMDb ID</label><input v-model="tz.tmdbId" type="number" placeholder="1396" /></div>
          <div class="field"><label class="label">Season</label><input v-model="tz.season" type="number" value="1" min="1" style="width:80px" /></div>
          <div class="field"><label class="label">Episode</label><input v-model="tz.ep" type="number" value="1" min="1" style="width:80px" /></div>
        </div>
        <div style="margin-bottom:14px">
          <div class="label" style="margin-bottom:6px">Request URL</div>
          <code class="url-preview">{{ torznabUrl }}</code>
        </div>
        <div class="actions">
          <button class="btn" :disabled="tz.loading" @click="tzSearch">
            {{ tz.loading ? 'Searching…' : '▶ Send' }}
          </button>
        </div>
        <div class="results">
          <p v-if="tz.loading" class="muted">Searching…</p>
          <p v-else-if="tz.error" class="red xs">{{ tz.error }}</p>
          <table v-else-if="tz.items.length" class="tbl">
            <thead><tr><th>Title</th><th>TMDb ID</th><th>Size</th><th>Grab URL</th></tr></thead>
            <tbody>
              <tr v-for="item in tz.items" :key="item.title">
                <td class="xs" style="max-width:340px">{{ item.title }}</td>
                <td class="muted xs">{{ item.tmdbid || '—' }}</td>
                <td class="muted xs">{{ item.size ? Math.round(item.size / 1048576) + ' MB' : '—' }}</td>
                <td><a v-if="item.link" :href="item.link" target="_blank" class="url-link">{{ item.link.slice(0, 100) }}{{ item.link.length > 100 ? '…' : '' }}</a><span v-else class="muted">—</span></td>
              </tr>
            </tbody>
          </table>
          <p v-else-if="tz.searched" class="muted">No results returned.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { sourceTest, torznabSearch, getConfig } from '../api'

const sr = reactive({
  tmdbId: '' as string | number,
  title: '',
  year: '' as string | number,
  mediaType: 'movie' as 'movie' | 'tv',
  season: '' as string | number,
  episode: '' as string | number,
  tvdbId: '' as string | number,
  loading: false,
  results: null as Record<string, import('../api').SourceResult> | null,
})

const tz = reactive({
  apiKey: '',
  type: 'movie' as 'movie' | 'tvsearch',
  q: '',
  year: '' as string | number,
  tmdbId: '' as string | number,
  imdbId: '',
  tvdbId: '' as string | number,
  season: 1 as number,
  ep: 1 as number,
  loading: false,
  searched: false,
  error: '',
  items: [] as { title: string; tmdbid: string; size: number; link: string }[],
})

const scanMsg = computed(() =>
  sr.mediaType === 'tv' && sr.season && !sr.episode
    ? `Scanning all episodes of S${String(sr.season).padStart(2, '0')}`
    : 'Resolving',
)

const torznabUrl = computed(() => {
  const p = new URLSearchParams({ t: tz.type, apikey: tz.apiKey })
  if (tz.q) p.set('q', String(tz.q))
  if (tz.type === 'movie') {
    if (tz.year) p.set('year', String(tz.year))
    if (tz.tmdbId) p.set('tmdbid', String(tz.tmdbId))
    if (tz.imdbId) p.set('imdbid', tz.imdbId)
  } else {
    if (tz.tvdbId) p.set('tvdbid', String(tz.tvdbId))
    if (tz.tmdbId) p.set('tmdbid', String(tz.tmdbId))
    if (tz.season) p.set('season', String(tz.season))
    if (tz.ep) p.set('ep', String(tz.ep))
  }
  return '/torznab/api?' + p.toString()
})

onMounted(async () => {
  try {
    const cfg = await getConfig()
    tz.apiKey = (cfg.torznab_api_key as string) || ''
  } catch {}
})

async function resolve() {
  if (!sr.tmdbId) { alert('Please enter a TMDb ID'); return }
  sr.loading = true
  sr.results = null
  try {
    const payload: import('../api').SourceTestRequest = {
      tmdb_id: Number(sr.tmdbId),
      media_type: sr.mediaType,
    }
    if (sr.title) payload.title = sr.title
    if (sr.year) payload.year = Number(sr.year)
    if (sr.mediaType === 'tv') {
      if (sr.season) payload.season = Number(sr.season)
      if (sr.episode) payload.episode = Number(sr.episode)
      if (sr.tvdbId) payload.tvdb_id = Number(sr.tvdbId)
    }
    sr.results = await sourceTest(payload)
  } finally {
    sr.loading = false
  }
}

async function tzSearch() {
  tz.loading = true
  tz.error = ''
  tz.items = []
  tz.searched = false
  try {
    const p = new URLSearchParams({ t: tz.type, apikey: tz.apiKey })
    if (tz.q) p.set('q', String(tz.q))
    if (tz.type === 'movie') {
      if (tz.year) p.set('year', String(tz.year))
      if (tz.tmdbId) p.set('tmdbid', String(tz.tmdbId))
      if (tz.imdbId) p.set('imdbid', tz.imdbId)
    } else {
      if (tz.tvdbId) p.set('tvdbid', String(tz.tvdbId))
      if (tz.tmdbId) p.set('tmdbid', String(tz.tmdbId))
      if (tz.season) p.set('season', String(tz.season))
      if (tz.ep) p.set('ep', String(tz.ep))
    }
    const xml = await torznabSearch(p)
    const doc = new DOMParser().parseFromString(xml, 'text/xml')
    const err = doc.querySelector('error')
    if (err) { tz.error = err.getAttribute('description') || xml; return }
    tz.items = Array.from(doc.querySelectorAll('item')).map(item => {
      const enc = item.querySelector('enclosure')
      const attrs: Record<string, string> = {}
      item.querySelectorAll('attr').forEach(a => { attrs[a.getAttribute('name')!] = a.getAttribute('value')! })
      return {
        title: item.querySelector('title')?.textContent || '',
        tmdbid: attrs.tmdbid || '',
        size: Number(enc?.getAttribute('length') || 0),
        link: enc?.getAttribute('url') || '',
      }
    })
    tz.searched = true
  } catch (e) {
    tz.error = String(e)
  } finally {
    tz.loading = false
  }
}
</script>

<style scoped>
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 16px; }
.card-header { padding: 16px 20px 0; }
.card-title { font-weight: 600; font-size: 15px; color: var(--text-bright); margin-bottom: 4px; }
.card-desc { font-size: 12px; color: var(--muted); margin-bottom: 12px; }
.card-body { padding: 16px 20px 20px; }
.row { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 14px; }
.field { display: flex; flex-direction: column; gap: 4px; }
.label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
input, select {
  background: var(--input-bg); border: 1px solid var(--border); border-radius: 5px;
  color: var(--text-bright); padding: 6px 10px; font-size: 13px; outline: none;
  min-width: 140px;
}
input:focus, select:focus { border-color: var(--accent); }
.actions { margin-bottom: 16px; }
.btn {
  background: var(--accent); color: #1e2127; font-weight: 600; font-size: 13px;
  border: none; border-radius: 5px; padding: 7px 18px; cursor: pointer;
}
.btn:disabled { opacity: .5; cursor: default; }
.results { min-height: 32px; }
.tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
.tbl th, .tbl td { padding: 5px 10px; border-bottom: 1px solid var(--border); text-align: left; }
.tbl th { color: var(--muted); font-size: 11px; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; }
.dot.ok { background: var(--green); }
.dot.err { background: var(--red); }
.name { font-weight: 500; font-size: 12px; white-space: nowrap; }
.muted { color: var(--muted); }
.red { color: var(--red); }
.xs { font-size: 11px; }
.pointer { cursor: pointer; }
.ep-link { font-size: 11px; color: var(--accent); margin-right: 6px; }
.url-row { padding: 1px 0; }
.url-link { font-size: 11px; color: var(--accent); word-break: break-all; }
.log-details { margin-top: 6px; }
.log-block {
  margin-top: 6px; background: var(--input-bg); border: 1px solid var(--border);
  border-radius: 5px; padding: 8px 10px;
  font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px;
  line-height: 1.4; color: var(--muted);
}
.url-preview {
  display: block; background: var(--input-bg); border: 1px solid var(--border);
  border-radius: 5px; padding: 8px 12px; font-size: 12px; word-break: break-all;
  color: var(--accent); min-height: 36px;
}
</style>
