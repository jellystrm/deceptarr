<template>
  <div>
    <div class="page-head">
      <div>
        <h1>Sources</h1>
        <p class="sub">Provider endpoints used to resolve a media reference into a playable stream. Order determines priority — first match wins.</p>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn ghost" @click="loadConfig" :disabled="saving">Discard</button>
        <button class="btn primary" @click="save" :disabled="saving">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13"/><polyline points="7 3 7 8 15 8"/></svg>
          {{ saving ? 'Saving…' : 'Save sources' }}
        </button>
      </div>
    </div>

    <!-- Active sources grid -->
    <div class="section-h" style="margin-bottom:14px">
      <div>
        <h2>Active sources <span class="num-pill">{{ order.length }}</span></h2>
        <p class="desc">Drag to reorder or use the arrows. First card is the primary source.</p>
      </div>
    </div>

    <div v-if="order.length" class="src-grid" style="margin-bottom:24px">
      <div
        v-for="(src, i) in order"
        :key="src"
        class="src-card"
        :class="{ 'drag-over': dragOverIdx === i }"
        draggable="true"
        @dragstart="dragStart(i)"
        @dragover.prevent="dragOver(i)"
        @drop="drop"
        @dragend="dragEnd"
      >
        <div :class="['src-mark', srcColor(src)]">{{ srcInitials(src) }}</div>
        <div class="src-meta">
          <div class="src-name">
            {{ src }}
            <span v-if="i === 0" class="pill teal flat">Primary</span>
            <span v-else class="pill gray flat">{{ ordinal(i + 1) }}</span>
          </div>
          <div class="src-url">{{ sourceUrl(src) }}</div>
        </div>
        <div class="src-actions">
          <button class="icon-mini" title="Move up" :disabled="i === 0" @click.stop="moveUp(i)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
          </button>
          <button class="icon-mini" title="Move down" :disabled="i >= order.length - 1" @click.stop="moveDown(i)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
        </div>
      </div>
    </div>

    <div v-else class="empty-state" style="margin-bottom:24px; min-height:180px">
      <h3>No active sources</h3>
      <p>Add built-in sources below to start resolving media.</p>
    </div>

    <!-- Save feedback -->
    <div v-if="saved || saveError" class="save-feedback">
      <span v-if="saved" style="font-size:12px;color:var(--green)">✓ Saved</span>
      <span v-if="saveError" style="font-size:12px;color:var(--red)">{{ saveError }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getConfig, saveSettings } from '../api'

const BUILTINS = ['kkphim', 'ophim', 'nguonc']
const BUILTIN_URLS: Record<string, string> = {
  kkphim: 'https://phimapi.com',
  ophim:  'https://ophim1.com',
  nguonc: 'https://phim.nguonc.com',
}
const SRC_COLORS: Record<string, string> = {
  kkphim: 'teal',
  ophim:  'blue',
  nguonc: 'purple',
}
const SRC_INITIALS: Record<string, string> = {
  kkphim: 'KK',
  ophim:  'OP',
  nguonc: 'NC',
}

const order     = ref<string[]>([])
const saving    = ref(false)
const saved     = ref(false)
const saveError = ref('')

function sourceUrl(name: string): string { return BUILTIN_URLS[name] || '' }
function srcColor(name: string): string  { return SRC_COLORS[name] || '' }
function srcInitials(name: string): string { return SRC_INITIALS[name] || name.slice(0, 2).toUpperCase() }
function ordinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return n + (s[(v - 20) % 10] || s[v] || s[0])
}

let dragIdx = -1
let dragOverIdx = ref(-1)

function dragStart(i: number) { dragIdx = i }
function dragOver(i: number)  { dragOverIdx.value = i }
function drop() {
  if (dragIdx < 0 || dragIdx === dragOverIdx.value) { dragEnd(); return }
  const arr = [...order.value]
  const [item] = arr.splice(dragIdx, 1)
  arr.splice(dragOverIdx.value, 0, item)
  order.value = arr
  dragEnd()
}
function dragEnd() { dragIdx = -1; dragOverIdx.value = -1 }

function moveUp(i: number) {
  if (i === 0) return
  const arr = [...order.value];
  [arr[i - 1], arr[i]] = [arr[i], arr[i - 1]]
  order.value = arr
}
function moveDown(i: number) {
  if (i >= order.value.length - 1) return
  const arr = [...order.value];
  [arr[i], arr[i + 1]] = [arr[i + 1], arr[i]]
  order.value = arr
}
function removeOrder(i: number) { order.value.splice(i, 1) }

async function save() {
  saving.value = true
  saveError.value = ''
  saved.value = false
  try {
    await saveSettings({
      _section: 'sources',
      source_order_json: JSON.stringify(order.value),
    })
    saved.value = true
    setTimeout(() => { saved.value = false }, 2500)
  } catch (e: unknown) {
    saveError.value = String(e)
  } finally {
    saving.value = false
  }
}

async function loadConfig() {
  try {
    const cfg = await getConfig()
    const saved = [...((cfg.source_order as string[] | undefined) || [])]
      .filter(name => BUILTINS.includes(name))
    // Ensure all builtins are always present — append any missing ones at the end
    const missing = BUILTINS.filter(b => !saved.includes(b))
    order.value = [...saved, ...missing]
  } catch {
    order.value = [...BUILTINS]
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.save-feedback {
  margin-top: 8px; font-size: 12px;
}
.src-card.inactive { opacity: .75; }
.src-card.drag-over { border-color: var(--teal); box-shadow: 0 0 0 2px rgba(94,224,189,.15); }
.icon-mini:disabled { opacity: .3; cursor: default; pointer-events: none; }
</style>
