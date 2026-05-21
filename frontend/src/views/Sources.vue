<template>
  <div>
    <div class="page-head">
      <div>
        <h1>Sources</h1>
        <p class="sub">Provider endpoints used to resolve media into streams. Order determines priority — first match wins.</p>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn ghost" @click="loadConfig" :disabled="saving">Discard</button>
        <button class="btn primary" @click="save" :disabled="saving">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13"/><polyline points="7 3 7 8 15 8"/></svg>
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
      </div>
    </div>

    <div v-if="saved || saveError" style="margin-bottom:12px">
      <span v-if="saved"     style="font-size:12px;color:var(--green)">✓ Saved</span>
      <span v-if="saveError" style="font-size:12px;color:var(--red)">{{ saveError }}</span>
    </div>

    <!-- Source list -->
    <div class="src-list">
      <div
        v-for="(src, i) in order"
        :key="src"
        class="src-row"
        :class="{ 'drag-over': dragOverIdx === i }"
        draggable="true"
        @dragstart="dragStart(i)"
        @dragover.prevent="dragOver(i)"
        @drop="drop"
        @dragend="dragEnd"
      >
        <!-- Source header -->
        <div class="src-hd">
          <div class="src-drag-handle">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>
              <line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
            </svg>
          </div>
          <div :class="['src-mark', srcColor(src)]">{{ srcInitials(src) }}</div>
          <div class="src-meta">
            <div class="src-name">
              {{ src }}
              <span v-if="i === 0" class="pos-dot primary" title="Primary source"></span>
              <span v-else class="pill gray flat xs">{{ ordinal(i + 1) }}</span>
            </div>
            <div class="src-url">{{ sourceUrl(src) }}</div>
          </div>
          <div class="src-order-btns">
            <button class="icon-mini" title="Move up" :disabled="i === 0" @click.stop="moveUp(i)">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
            </button>
            <button class="icon-mini" title="Move down" :disabled="i >= order.length - 1" @click.stop="moveDown(i)">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
          </div>
        </div>

        <!-- Variant priority + auto-download -->
        <div class="src-config">
          <!-- Variant chips (horizontal) -->
          <div class="var-row">
            <span class="var-row-label">Variant priority</span>
            <div class="var-chips">
              <div
                v-for="(variant, vi) in variantPriority[src]"
                :key="variant"
                class="var-chip"
              >
                <span class="var-rank">{{ vi + 1 }}</span>
                <span class="var-name">{{ variant }}</span>
                <button class="var-mv" title="← Higher priority" :disabled="vi === 0" @click="moveVariantLeft(src, vi)">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                </button>
                <button class="var-mv" title="→ Lower priority" :disabled="vi >= variantPriority[src].length - 1" @click="moveVariantRight(src, vi)">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Auto-download toggle -->
          <div class="auto-dl-row">
            <label class="check">
              <input type="checkbox" v-model="autoDownload[src]" />
              <span class="check-box"></span>
              <span>Auto-download</span>
            </label>
            <span v-if="autoDownload[src]" class="auto-hint">
              grabs <b>{{ variantPriority[src]?.[0] }}</b> automatically when found
            </span>
            <span v-else class="auto-hint muted">manual only</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
const DEFAULT_VARIANTS = ['Vietsub', 'Lồng tiếng', 'Thuyết minh']

const order           = ref<string[]>([])
const variantPriority = ref<Record<string, string[]>>({})
const autoDownload    = ref<Record<string, boolean>>({})
const saving          = ref(false)
const saved           = ref(false)
const saveError       = ref('')

function sourceUrl(name: string)   { return BUILTIN_URLS[name] || '' }
function srcColor(name: string)    { return SRC_COLORS[name] || '' }
function srcInitials(name: string) { return SRC_INITIALS[name] || name.slice(0, 2).toUpperCase() }
function ordinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return n + (s[(v - 20) % 10] || s[v] || s[0])
}

// ── Drag-to-reorder source order ──────────────────────────────────────────────
let dragIdx = -1
const dragOverIdx = ref(-1)

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

// ── Variant reorder (horizontal ← →) ─────────────────────────────────────────
function moveVariantLeft(src: string, i: number) {
  if (i === 0) return
  const arr = [...variantPriority.value[src]]
  ;[arr[i - 1], arr[i]] = [arr[i], arr[i - 1]]
  variantPriority.value = { ...variantPriority.value, [src]: arr }
}
function moveVariantRight(src: string, i: number) {
  const arr = variantPriority.value[src] || []
  if (i >= arr.length - 1) return
  const narr = [...arr]
  ;[narr[i], narr[i + 1]] = [narr[i + 1], narr[i]]
  variantPriority.value = { ...variantPriority.value, [src]: narr }
}

// ── Save all ──────────────────────────────────────────────────────────────────
async function save() {
  saving.value = true
  saveError.value = ''
  saved.value = false
  try {
    await saveSettings({
      _section: 'sources',
      source_order_json: JSON.stringify(order.value),
      source_variant_priority_json: JSON.stringify(variantPriority.value),
      source_auto_download_json: JSON.stringify(autoDownload.value),
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

    // source order
    const savedOrder = [...((cfg.source_order as string[] | undefined) || [])]
      .filter(name => BUILTINS.includes(name))
    const missing = BUILTINS.filter(b => !savedOrder.includes(b))
    order.value = [...savedOrder, ...missing]

    // variant priority
    const rawVP = (cfg.source_variant_priority as Record<string, string[]> | undefined) || {}
    const vp: Record<string, string[]> = {}
    for (const src of BUILTINS) {
      const s = rawVP[src]
      vp[src] = Array.isArray(s) && s.length ? s : [...DEFAULT_VARIANTS]
    }
    variantPriority.value = vp

    // auto-download flags
    const rawAD = (cfg.source_auto_download as Record<string, boolean> | undefined) || {}
    const ad: Record<string, boolean> = {}
    for (const src of BUILTINS) ad[src] = Boolean(rawAD[src])
    autoDownload.value = ad

  } catch {
    order.value = [...BUILTINS]
    const vp: Record<string, string[]> = {}
    const ad: Record<string, boolean> = {}
    for (const src of BUILTINS) { vp[src] = [...DEFAULT_VARIANTS]; ad[src] = false }
    variantPriority.value = vp
    autoDownload.value = ad
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.src-list { display: flex; flex-direction: column; gap: 10px; }

.src-row {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); overflow: hidden; transition: border-color .12s;
}
.src-row:hover { border-color: var(--border-2); }
.src-row.drag-over { border-color: var(--teal); box-shadow: 0 0 0 2px rgba(94,224,189,.15); }

/* Header */
.src-hd {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 16px; cursor: grab;
}
.src-hd:active { cursor: grabbing; }
.src-drag-handle { color: var(--text-3); flex-shrink: 0; display: flex; align-items: center; }
.src-meta { flex: 1; min-width: 0; }
.src-name { font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 8px; }
.src-url  { font-family: var(--font-mono); font-size: 11.5px; color: var(--text-3); margin-top: 2px; }
.src-order-btns { display: flex; gap: 4px; }

.pos-dot {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.pos-dot.primary {
  background: var(--teal);
  box-shadow: 0 0 0 2px rgba(94,224,189,.2), 0 0 5px rgba(94,224,189,.4);
}
.pill.xs { padding: 2px 7px; font-size: 10.5px; }

/* Config row (variants + auto-dl) */
.src-config {
  border-top: 1px solid var(--border); background: var(--bg-2);
  padding: 12px 16px 12px 52px;
  display: flex; flex-direction: column; gap: 10px;
}

/* Horizontal variant chips */
.var-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.var-row-label {
  font: 600 11px/1 var(--font-mono); letter-spacing: .07em; text-transform: uppercase;
  color: var(--text-3); white-space: nowrap; flex-shrink: 0;
}
.var-chips { display: flex; gap: 6px; flex-wrap: wrap; }

.var-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 8px 4px 6px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 6px; font-size: 12.5px;
}
.var-rank {
  font-family: var(--font-mono); font-size: 10px; color: var(--text-3);
  min-width: 10px; text-align: center;
}
.var-name { font-weight: 500; color: var(--text); }
.var-mv {
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px; border-radius: 4px; border: none;
  background: transparent; color: var(--text-3); cursor: pointer;
  transition: background .1s, color .1s; padding: 0;
}
.var-mv:hover:not(:disabled) { background: var(--surface-2); color: var(--text); }
.var-mv:disabled { opacity: .25; cursor: default; }

/* Auto-download row */
.auto-dl-row { display: flex; align-items: center; gap: 10px; }
.auto-hint { font-size: 12px; color: var(--text-3); }
.auto-hint b { color: var(--teal); font-weight: 600; }
.auto-hint.muted { color: var(--muted, var(--text-3)); opacity: .6; }
</style>
