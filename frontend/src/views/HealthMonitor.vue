<template>
  <div>
    <div class="page-head">
      <div>
        <h1>Health &amp; Monitor</h1>
        <p class="sub">Service health and a dry-run sandbox to simulate the LinkGrabber → resolve flow without touching your queue.</p>
      </div>
      <button class="btn" :disabled="healthRunning" @click="runHealth(true)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        {{ healthRunning ? 'Checking…' : 'Run health check' }}
      </button>
    </div>

    <!-- ── Health ── -->
    <div class="section-h">
      <div>
        <h2>Health <span class="num-pill">6 services</span></h2>
        <p class="desc">Click a tile to re-check a single service.</p>
      </div>
    </div>

    <div class="health-grid">
      <div
        v-for="tile in tiles"
        :key="tile.name"
        class="health-tile"
        @click="runSingle(tile.name)"
      >
        <div class="health-tile-head">
          <span class="name">{{ tile.label }}</span>
          <span :class="['dot', tile.dotClass]"></span>
        </div>
        <span class="desc">
          <template v-if="tile.status === 'loading'">checking…</template>
          <template v-else-if="tile.status === 'ok'">{{ tile.urlShort }} · {{ tile.latency }}ms</template>
          <template v-else-if="tile.status === 'warn'">{{ tile.urlShort }} · {{ tile.latency }}ms (slow)</template>
          <template v-else-if="tile.status === 'error'">{{ tile.message || 'unreachable' }}</template>
          <template v-else>click to test</template>
        </span>
      </div>
    </div>

    <!-- ── Output paths ── -->
    <div class="section-h" style="margin-top:28px">
      <div>
        <h2>Output paths <span class="num-pill">dry-run</span></h2>
        <p class="desc">Preview where STRM files and HLS-DL downloads will be written before Radarr/Sonarr import scans run.</p>
      </div>
      <button class="btn sm" :disabled="pathChecking" @click="testOutputPaths">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        {{ pathChecking ? 'Checking…' : 'Test output paths' }}
      </button>
    </div>

    <div class="fcard" style="margin-bottom:18px">
      <div class="fcard-body" style="padding:14px 16px">
        <div v-if="!pathRows.length" class="path-empty">Run the path test to preview configured output locations.</div>
        <div v-else class="path-grid">
          <div v-for="row in pathRows" :key="row.key" class="path-row">
            <div>
              <div class="path-label">{{ row.label }}</div>
              <div class="path-owner">{{ row.owner }}</div>
            </div>
            <code>{{ row.path }}</code>
          </div>
        </div>
        <div v-if="pathWarnings.length" class="path-warnings">
          <div v-for="warning in pathWarnings" :key="warning">⚠ {{ warning }}</div>
        </div>
      </div>
    </div>

    <!-- ── Testing sandbox ── -->
    <div class="section-h" style="margin-top:28px">
      <div>
        <h2>Testing sandbox <span class="num-pill">dry-run</span></h2>
        <p class="desc">Enter a TMDB reference, then simulate the grabber or test each source resolver. Nothing is queued or written to disk.</p>
      </div>
    </div>

    <div class="fcard" style="margin-bottom:18px">
      <div class="fcard-head">
        <div class="fcard-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
        </div>
        <div>
          <h3>Media reference</h3>
          <p class="desc">Switch to TV Series to enter season / episode.</p>
        </div>
        <div style="margin-left:auto">
          <div class="seg-radio">
            <button :class="{ active: mediaType === 'movie' }" @click="mediaType = 'movie'">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><line x1="7" y1="4" x2="7" y2="20"/><line x1="17" y1="4" x2="17" y2="20"/></svg>
              Movie
            </button>
            <button :class="{ active: mediaType === 'tv' }" @click="mediaType = 'tv'">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="15" rx="2"/><polyline points="17 2 12 7 7 2"/></svg>
              TV Series
            </button>
          </div>
        </div>
      </div>
      <div class="fcard-body">
        <div class="form">
          <div class="field">
            <label>TMDB ID <span class="hint">required</span></label>
            <input v-model="tmdbId" class="input mono" type="number" :placeholder="defaults.tmdbId" />
          </div>
          <div class="field">
            <label>Title <span class="hint">fuzzy match</span></label>
            <input v-model="title" class="input" :placeholder="defaults.title" />
          </div>
          <template v-if="mediaType === 'tv'">
            <div class="field">
              <label>Season <span class="hint">optional</span></label>
              <input v-model="season" class="input mono" type="number" placeholder="all" />
            </div>
            <div class="field">
              <label>Episode <span class="hint">optional</span></label>
              <input v-model="episode" class="input mono" type="number" placeholder="all" />
            </div>
          </template>
        </div>
      </div>
      <div class="fcard-foot">
        <span style="display:inline-flex;align-items:center;gap:6px;font-size:12px">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          Dry-run · nothing is queued or written to disk
        </span>
        <div style="margin-left:auto;display:flex;gap:8px">
          <button class="btn sm" :disabled="resolving" @click="resolveSources">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            {{ resolving ? 'Resolving…' : 'Test all sources' }}
          </button>
          <button class="btn primary sm" :disabled="testingIndexer" @click="testTorznab">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
            {{ testingIndexer ? 'Testing…' : 'Test indexer' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Resolve on source ── -->
    <div class="section-h">
      <div>
        <h2>Resolve on source <span class="num-pill">3 sources</span></h2>
        <p class="desc">Run the resolver pipeline against one source at a time. Useful for diagnosing "No match" errors.</p>
      </div>
    </div>

    <div class="fcard" style="margin-bottom:18px">
      <div class="fcard-body" style="padding:14px 16px">
        <div
          v-for="(src, i) in srcTests"
          :key="src.name"
          class="src-test"
        >
          <div class="src-test-badge">{{ String(i + 1).padStart(2, '0') }}</div>
          <div class="src-test-meta">
            <div class="n">
              {{ src.name }}
              <span v-if="i === 0" class="pill teal flat">Primary</span>
            </div>
            <div class="u">{{ src.url }}</div>
          </div>
          <div class="actions">
            <span class="result" :class="src.resultClass">{{ src.resultText }}</span>
            <button class="btn sm" :disabled="src.loading" @click="testSingleSource(src.name)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              {{ src.loading ? 'Testing…' : 'Test resolve' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Run output ── -->
    <div class="section-h">
      <div>
        <h2>Run output</h2>
        <p class="desc">Live log from health check + sandbox actions in this session.</p>
      </div>
      <div style="display:flex;gap:6px">
        <button class="btn ghost sm" @click="copyLog">Copy</button>
        <button class="btn ghost sm" @click="clearLog">Clear</button>
      </div>
    </div>

    <div class="fcard">
      <div style="padding:14px 16px">
        <div class="testlog" ref="logEl">
          <div v-if="!logLines.length" class="l-info">
            <span class="ts">–</span>No test action has run yet. Run a health check or use the sandbox above.
          </div>
          <div v-for="(line, i) in logLines" :key="i" :class="line.cls">
            <span class="ts">{{ line.ts }}</span>{{ line.text }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { getHealth, sourceTest, testIndexer, checkOutputPaths, type HealthResult, type SourceTestRequest, type SourceResult } from '../api'

interface Tile {
  name: string; label: string; url: string; urlShort: string
  status: 'idle' | 'loading' | 'ok' | 'warn' | 'error' | 'unknown'
  dotClass: string; latency: number | null; message: string
}
interface SrcTest {
  name: string; url: string
  loading: boolean; resultText: string; resultClass: string
}
interface LogLine { cls: string; ts: string; text: string }

const SERVICES: { name: string; label: string }[] = [
  { name: 'radarr',   label: 'Radarr'   },
  { name: 'sonarr',   label: 'Sonarr'   },
  { name: 'jellyfin', label: 'Jellyfin' },
  { name: 'kkphim',   label: 'kkphim'   },
  { name: 'ophim',    label: 'ophim'    },
  { name: 'nguonc',   label: 'nguonc'   },
]

const SRC_URLS: Record<string, string> = {
  kkphim: 'https://phimapi.com',
  ophim:  'https://ophim1.com',
  nguonc: 'https://phim.nguonc.com',
}

const tiles = reactive<Tile[]>(
  SERVICES.map(s => ({
    ...s, url: '', urlShort: '', status: 'idle', dotClass: 'gray', latency: null, message: '',
  }))
)

const srcTests = reactive<SrcTest[]>(
  ['kkphim', 'ophim', 'nguonc'].map(name => ({
    name, url: SRC_URLS[name] || '',
    loading: false, resultText: '· not run yet', resultClass: '',
  }))
)

const mediaType     = ref<'movie' | 'tv'>('movie')
const tmdbId        = ref('')
const title         = ref('')
const year          = ref('')
const season        = ref('')
const episode       = ref('')
const healthRunning  = ref(false)
const testingIndexer = ref(false)
const resolving      = ref(false)
const pathChecking   = ref(false)
const pathRows       = ref<{ key: string; label: string; owner: string; path: string }[]>([])
const pathWarnings   = ref<string[]>([])
const logLines       = ref<LogLine[]>([])
const logEl          = ref<HTMLElement | null>(null)

const DEFAULTS = {
  movie: { tmdbId: '27205', title: 'Inception', year: '2010' },
  tv:    { tmdbId: '37854', title: 'One Piece',  year: '1999' },
} as const

const defaults = computed(() => DEFAULTS[mediaType.value])

function valueOrDefault(value: string, fallback: string) { return value.trim() || fallback }
function intVal(value: string): number | undefined {
  const n = Number(value)
  return Number.isFinite(n) && value.trim() !== '' ? n : undefined
}

const payload = computed<SourceTestRequest>(() => {
  const p: SourceTestRequest = { media_type: mediaType.value }
  const id = intVal(valueOrDefault(tmdbId.value, defaults.value.tmdbId))
  const yr = intVal(valueOrDefault(year.value, defaults.value.year))
  if (id !== undefined) p.tmdb_id = id
  p.title = valueOrDefault(title.value, defaults.value.title)
  if (yr !== undefined) p.year = yr
  if (mediaType.value === 'tv') {
    const s = intVal(season.value)
    const ep = intVal(episode.value)
    if (s !== undefined) p.season = s
    if (ep !== undefined) p.episode = ep
  }
  return p
})

function now() { return new Date().toTimeString().slice(0, 8) }

function addLog(cls: string, text: string) {
  logLines.value.push({ cls, ts: now(), text })
  nextTick(() => {
    if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
  })
}

function clearLog() { logLines.value = [] }

async function copyLog() {
  const text = logLines.value.map(l => `[${l.ts}] ${l.text}`).join('\n')
  try { await navigator.clipboard.writeText(text) } catch {}
}

function urlShort(url: string): string {
  try { return new URL(url).hostname } catch { return url }
}

function applyHealthResult(name: string, result: HealthResult, log = true) {
  const tile = tiles.find(t => t.name === name)
  if (!tile) return
  tile.url = result.url || ''
  tile.urlShort = urlShort(result.url || '')
  tile.latency = result.latency
  tile.message = result.message || ''
  tile.status = result.status

  if (result.status === 'ok') {
    tile.dotClass = 'green'
    if (log) addLog('l-ok', `${name.padEnd(9)} → ${urlShort(result.url || '')} · ${result.latency}ms`)
  } else if (result.status === 'warn') {
    tile.dotClass = 'amber'
    if (log) addLog('l-warn', `${name.padEnd(9)} → ${urlShort(result.url || '')} · ${result.latency}ms (slow)`)
  } else if (result.status === 'error') {
    tile.dotClass = 'red'
    if (log) addLog('l-err', `${name.padEnd(9)} → ${result.message || 'unreachable'}`)
  } else {
    tile.dotClass = 'gray'
    if (log) addLog('l-info', `${name.padEnd(9)} → not configured`)
  }
}

async function runHealth(log = false) {
  if (healthRunning.value) return
  healthRunning.value = true
  tiles.forEach(t => { t.status = 'loading'; t.dotClass = 'gray' })
  if (log) addLog('l-info', '── Health check ──')
  try {
    const results = await getHealth()
    for (const [name, result] of Object.entries(results)) applyHealthResult(name, result, log)
  } catch (e) {
    if (log) addLog('l-err', `Health check failed: ${e}`)
    tiles.forEach(t => { if (t.status === 'loading') { t.status = 'error'; t.dotClass = 'red' } })
  } finally {
    healthRunning.value = false
  }
}

async function runSingle(name: string) {
  const tile = tiles.find(t => t.name === name)
  if (!tile) return
  tile.status = 'loading'; tile.dotClass = 'gray'
  try {
    const results = await getHealth()
    const result = results[name]
    if (result) applyHealthResult(name, result, false)
  } catch (e) {
    tile.status = 'error'; tile.dotClass = 'red'; tile.message = String(e)
  }
}

async function testOutputPaths() {
  if (pathChecking.value) return
  pathChecking.value = true
  addLog('l-info', '── Output path dry-run ──')
  try {
    const result = await checkOutputPaths()
    pathRows.value = result.paths
    pathWarnings.value = result.warnings || []
    addLog('l-info', `download root: ${result.roots.download_root}`)
    addLog('l-info', `movie STRM root: ${result.roots.movie_strm_root}`)
    addLog('l-info', `series STRM root: ${result.roots.series_strm_root}`)
    for (const row of result.paths) addLog('l-ok', `${row.label.padEnd(14)} → ${row.path}`)
    for (const warning of pathWarnings.value) addLog('l-warn', warning)
  } catch (e) {
    addLog('l-err', `Output path test failed: ${e}`)
  } finally {
    pathChecking.value = false
  }
}

async function testTorznab() {
  testingIndexer.value = true
  addLog('l-info', `── Test Indexer · ${describePayload()} ──`)
  try {
    const res = await testIndexer(payload.value)
    addLog('l-info', `request: ${res.url}`)
    addLog(res.count > 0 ? 'l-ok' : 'l-err', `Indexer returned ${res.count} result(s)`)
    for (const item of res.results.slice(0, 10)) addLog('l-info', `  ${item}`)
    if (res.results.length > 10) addLog('l-info', `  … ${res.results.length - 10} more`)
  } catch (e) {
    addLog('l-err', `Test Indexer failed: ${e}`)
  } finally {
    testingIndexer.value = false
  }
}

async function resolveSources() {
  resolving.value = true
  addLog('l-info', `── Resolve sources · ${describePayload()} ──`)
  srcTests.forEach(s => { s.loading = true; s.resultText = '… resolving'; s.resultClass = '' })
  try {
    const results = await sourceTest(payload.value)
    for (const src of srcTests) {
      src.loading = false
      const result = results[src.name]
      if (result) {
        applySrcResult(src, result)
        logSourceResult(src.name, result)
      } else {
        src.resultText = '· no result'; src.resultClass = ''
      }
    }
  } catch (e) {
    addLog('l-err', `Resolve failed: ${e}`)
    srcTests.forEach(s => { s.loading = false; s.resultText = '· failed'; s.resultClass = 'err' })
  } finally {
    resolving.value = false
  }
}

async function testSingleSource(name: string) {
  const src = srcTests.find(s => s.name === name)
  if (!src) return
  src.loading = true; src.resultText = '… resolving'; src.resultClass = ''
  addLog('l-info', `── Resolve ${name} · ${describePayload()} ──`)
  try {
    const results = await sourceTest(payload.value)
    src.loading = false
    const result = results[name]
    if (result) {
      applySrcResult(src, result)
      logSourceResult(name, result)
    } else {
      src.resultText = '· no result'; src.resultClass = ''
    }
  } catch (e) {
    src.loading = false; src.resultText = '· failed'; src.resultClass = 'err'
    addLog('l-err', `${name} → ${e}`)
  }
}

function applySrcResult(src: SrcTest, result: SourceResult) {
  if (result.status === 'ok') {
    const urls = result.urls || (result.url ? [{ url: result.url }] : [])
    const found = result.episodes ? `${result.found || 0}/${result.total || 0} ep` : `${urls.length || 1} URL(s)`
    src.resultText = `✓ matched · ${found}`
    src.resultClass = 'ok'
  } else {
    src.resultText = `✗ ${result.message || 'not found'}`
    src.resultClass = 'err'
  }
}

function logSourceResult(name: string, result: SourceResult) {
  if (result.status === 'ok') {
    const urls = result.urls || (result.url ? [{ url: result.url }] : [])
    const found = result.episodes ? `${result.found || 0}/${result.total || 0} episode(s)` : `${urls.length || 1} URL(s)`
    addLog('l-ok', `${name.padEnd(9)} → ${found}`)
    for (const hit of urls.slice(0, 6)) {
      const label = [hit.server, hit.name].filter(Boolean).join(' / ')
      addLog('l-info', `  ${label ? label + ' · ' : ''}${hit.url}`)
    }
    if (result.episodes) {
      for (const ep of result.episodes.filter((e: { url?: string | null }) => e.url).slice(0, 12)) {
        const prefix = ep.season
          ? `S${String(ep.season).padStart(2, '0')}E${String(ep.num).padStart(2, '0')}`
          : `E${String(ep.num).padStart(2, '0')}`
        addLog('l-info', `  ${prefix} · ${ep.url}`)
      }
    }
  } else {
    addLog('l-err', `${name.padEnd(9)} → ${result.message || 'Not found'}`)
  }
  for (const line of (result.log || []).slice(0, 18)) addLog('l-trace', `  ${line}`)
}

function describePayload() {
  const p = payload.value
  const id = p.tmdb_id ? `TMDB ${p.tmdb_id}` : 'no TMDB'
  const name = p.title ? `"${p.title}"` : id
  if (p.media_type === 'tv') {
    const seasonLabel = p.season ? `S${String(p.season).padStart(2, '0')}` : 'all seasons'
    const epLabel = p.episode ? `E${String(p.episode).padStart(2, '0')}` : 'all episodes'
    return `${name} ${seasonLabel} ${epLabel}`
  }
  return name
}

onMounted(() => runHealth(false))
</script>

<style scoped>
.path-empty {
  color: var(--text-3);
  font-size: 13px;
}
.path-grid {
  display: grid;
  gap: 8px;
}
.path-row {
  display: grid;
  grid-template-columns: minmax(150px, 220px) minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: rgba(255,255,255,.02);
}
.path-label {
  color: var(--text);
  font-size: 13px;
  font-weight: 700;
}
.path-owner {
  margin-top: 3px;
  color: var(--text-3);
  font-size: 12px;
}
.path-row code {
  min-width: 0;
  overflow-wrap: anywhere;
  color: var(--text-2);
  font-family: var(--font-mono);
  font-size: 12px;
}
.path-warnings {
  display: grid;
  gap: 4px;
  margin-top: 10px;
  color: var(--amber);
  font-size: 12px;
}
/* Log trace lines */
:global(.testlog .l-trace) { color: var(--text-3); }
@media (max-width: 720px) {
  .path-row { grid-template-columns: 1fr; }
}
</style>
