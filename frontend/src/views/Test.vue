<template>
  <div>
    <div class="page-head">
      <div>
        <h1>Test</h1>
        <p class="sub">Run integration checks against every external service Deceptarr depends on. Use this after a config change or when something looks off.</p>
      </div>
      <button class="btn primary" :disabled="running" @click="runChecks">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        {{ running ? 'Running…' : 'Run all tests' }}
      </button>
    </div>

    <!-- Health tiles -->
    <div class="test-grid">
      <div
        v-for="tile in tiles"
        :key="tile.name"
        class="test-tile"
        @click="runSingle(tile.name)"
      >
        <div class="test-tile-head">
          <span class="name">{{ tile.label }}</span>
          <span :class="['dot', tile.dotClass]"></span>
        </div>
        <span class="desc">
          <template v-if="tile.status === 'loading'">checking…</template>
          <template v-else-if="tile.status === 'ok'">{{ tile.url }} · {{ tile.latency }}ms</template>
          <template v-else-if="tile.status === 'warn'">{{ tile.url }} · {{ tile.latency }}ms (slow)</template>
          <template v-else-if="tile.status === 'error'">{{ tile.message || 'unreachable' }}</template>
          <template v-else>click to test</template>
        </span>
      </div>
    </div>

    <!-- Run log -->
    <div class="card">
      <div class="card-head">
        <div>
          <h2>Run output <span style="color:var(--text-3);font-weight:500">{{ lastRun ? '· ' + lastRun : '' }}</span></h2>
          <p class="desc">Combined log from the last full test pass.</p>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn ghost sm" @click="clearLog">Clear</button>
        </div>
      </div>
      <div class="card-body" style="padding:14px 16px">
        <div class="testlog" ref="logEl">
          <div v-if="!logLines.length" class="l-info">
            <span class="ts">—</span>No tests run yet. Click "Run all tests" to start.
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
import { ref, reactive, nextTick, onMounted } from 'vue'
import { getHealth, type HealthResult } from '../api'

interface Tile {
  name: string
  label: string
  url: string
  status: 'idle' | 'loading' | 'ok' | 'warn' | 'error' | 'unknown'
  dotClass: string
  latency: number | null
  message: string
}

interface LogLine { cls: string; ts: string; text: string }

const SERVICES: { name: string; label: string }[] = [
  { name: 'radarr',  label: 'Radarr'  },
  { name: 'sonarr',  label: 'Sonarr'  },
  { name: 'jellyfin',label: 'Jellyfin'},
  { name: 'kkphim',  label: 'kkphim'  },
  { name: 'ophim',   label: 'ophim'   },
  { name: 'nguonc',  label: 'nguonc'  },
]

const tiles = reactive<Tile[]>(
  SERVICES.map(s => ({
    ...s, url: '', status: 'idle', dotClass: 'gray', latency: null, message: '',
  }))
)

const running  = ref(false)
const logLines = ref<LogLine[]>([])
const lastRun  = ref('')
const logEl    = ref<HTMLElement | null>(null)

function now() {
  return new Date().toTimeString().slice(0, 8)
}

function addLog(cls: string, text: string) {
  logLines.value.push({ cls, ts: now(), text })
  nextTick(() => {
    if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
  })
}

function clearLog() { logLines.value = [] }

function applyResult(name: string, result: HealthResult) {
  const tile = tiles.find(t => t.name === name)
  if (!tile) return
  tile.url     = result.url || ''
  tile.latency = result.latency
  tile.message = result.message || ''
  tile.status  = result.status

  if (result.status === 'ok') {
    tile.dotClass = 'green'
    addLog('l-ok', `${name.padEnd(8)} → ${result.url} · ${result.latency}ms`)
  } else if (result.status === 'warn') {
    tile.dotClass = 'amber'
    addLog('l-warn', `${name.padEnd(8)} → ${result.url} · ${result.latency}ms (slow)`)
  } else if (result.status === 'error') {
    tile.dotClass = 'red'
    addLog('l-err', `${name.padEnd(8)} → ${result.message || 'unreachable'}`)
  } else {
    tile.dotClass = 'gray'
    addLog('l-info', `${name.padEnd(8)} → not configured`)
  }
}

async function runChecks() {
  if (running.value) return
  running.value = true
  logLines.value = []
  lastRun.value = ''

  // Set all tiles to loading
  tiles.forEach(t => { t.status = 'loading'; t.dotClass = 'gray' })
  addLog('l-info', 'Starting integration tests…')

  try {
    const results = await getHealth()
    let ok = 0, warn = 0, err = 0
    for (const [name, result] of Object.entries(results)) {
      applyResult(name, result)
      if (result.status === 'ok')      ok++
      else if (result.status === 'warn') warn++
      else if (result.status === 'error') err++
    }
    addLog('l-info', `${ok} ok · ${warn} warnings · ${err} errors`)
    lastRun.value = 'just now'
  } catch (e) {
    addLog('l-err', `Failed to run health check: ${e}`)
    tiles.forEach(t => { t.status = 'idle'; t.dotClass = 'gray' })
  } finally {
    running.value = false
  }
}

async function runSingle(name: string) {
  const tile = tiles.find(t => t.name === name)
  if (!tile) return
  tile.status = 'loading'; tile.dotClass = 'gray'
  addLog('l-info', `Testing ${name}…`)
  try {
    const results = await getHealth()
    const result = results[name]
    if (result) applyResult(name, result)
  } catch (e) {
    tile.status = 'error'; tile.dotClass = 'red'
    addLog('l-err', `${name} → ${e}`)
  }
}

onMounted(() => {
  // Auto-run on mount so tiles show current state
  runChecks()
})
</script>
