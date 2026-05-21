<template>
  <div>
    <div class="page-head">
      <div>
        <h1>Sources</h1>
        <p class="sub">Provider endpoints used to resolve media into streams. Order determines priority — first match wins.</p>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn ghost" @click="loadConfig" :disabled="saving">Discard</button>
        <button class="btn primary" @click="save" :disabled="saving || !isDirty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13"/><polyline points="7 3 7 8 15 8"/></svg>
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
      </div>
    </div>

    <div v-if="saved || saveError" style="margin-bottom:12px">
      <span v-if="saved"     style="font-size:12px;color:var(--green)">✓ Saved</span>
      <span v-if="saveError" style="font-size:12px;color:var(--red)">{{ saveError }}</span>
    </div>

  <!-- Unsaved changes confirm modal -->
  <teleport to="body">
    <div v-if="confirmVisible" class="confirm-overlay" @click.self="confirmStay">
      <div class="confirm-box">
        <div class="confirm-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </div>
        <div class="confirm-body">
          <p class="confirm-title">Unsaved changes</p>
          <p class="confirm-msg">You have unsaved changes in Sources. Save before leaving?</p>
        </div>
        <div class="confirm-actions">
          <button class="btn ghost sm" @click="confirmStay">Stay</button>
          <button class="btn sm" @click="confirmDiscard">Discard</button>
          <button class="btn primary sm" @click="confirmDoSave">Save &amp; continue</button>
        </div>
      </div>
    </div>
  </teleport>

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

        <!-- Variant config section -->
        <div class="src-variants">
          <div
            v-for="(variant, vi) in variantConfig[src]"
            :key="variant.name"
            class="variant-card"
          >
            <!-- Variant header -->
            <div class="variant-hd">
              <span class="variant-rank">{{ vi + 1 }}</span>
              <span class="variant-name">{{ variant.name }}</span>
              <div class="variant-mv-btns">
                <button class="icon-mini xs" title="Move left" :disabled="vi === 0" @click="moveVariantUp(src, vi)">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                </button>
                <button class="icon-mini xs" title="Move right" :disabled="vi >= variantConfig[src].length - 1" @click="moveVariantDown(src, vi)">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                </button>
              </div>
            </div>

            <!-- Type rows — ordered, reorderable -->
            <div class="type-rows">
              <div
                v-for="(te, ti) in variant.types"
                :key="te.key"
                class="type-row"
                :class="{ 'type-enabled': te.auto_download }"
              >
                <label class="check type-check">
                  <input type="checkbox" v-model="te.auto_download" />
                  <span class="check-box"></span>
                  <span class="check-lbl">Auto download</span>
                </label>
                <span class="type-badge" :class="te.key">{{ te.key === 'strm' ? 'STRM' : 'HLS-DL' }}</span>
                <div class="type-mv-btns">
                  <button class="icon-mini xs" title="Higher priority" :disabled="ti === 0" @click="moveTypeUp(src, vi, ti)">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
                  </button>
                  <button class="icon-mini xs" title="Lower priority" :disabled="ti >= variant.types.length - 1" @click="moveTypeDown(src, vi, ti)">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { getConfig, saveSettings } from '../api'

type TypeKey = 'strm' | 'hls_dl'
interface TypeEntry    { key: TypeKey; auto_download: boolean }
interface VariantConfig { name: string; types: TypeEntry[] }

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
const DEFAULT_VARIANT_NAMES = ['Vietsub', 'Lồng tiếng', 'Thuyết minh']

function defaultTypes(): TypeEntry[] {
  return [
    { key: 'strm',   auto_download: false },
    { key: 'hls_dl', auto_download: false },
  ]
}
function defaultVariant(name: string): VariantConfig {
  return { name, types: defaultTypes() }
}
function defaultVariants(): VariantConfig[] {
  return DEFAULT_VARIANT_NAMES.map(defaultVariant)
}

/** Convert UI VariantConfig to backend format (priority = position index) */
function toBackendVariant(v: VariantConfig): Record<string, unknown> {
  const result: Record<string, unknown> = { name: v.name }
  v.types.forEach((t, i) => {
    result[t.key] = { auto_download: t.auto_download, priority: i + 1 }
  })
  return result
}

/** Parse backend variant object into UI VariantConfig (sort by priority) */
function fromBackendVariant(raw: Record<string, unknown>): VariantConfig {
  const entries: Array<{ key: TypeKey; auto_download: boolean; priority: number }> = []
  for (const key of ['strm', 'hls_dl'] as TypeKey[]) {
    const tc = ((raw[key] ?? {}) as Record<string, unknown>)
    entries.push({
      key,
      auto_download: Boolean(tc.auto_download),
      priority: Number(tc.priority) || 99,
    })
  }
  entries.sort((a, b) => a.priority - b.priority)
  return {
    name: String(raw.name || ''),
    types: entries.map(e => ({ key: e.key, auto_download: e.auto_download })),
  }
}

const order         = ref<string[]>([])
const variantConfig = ref<Record<string, VariantConfig[]>>({})
const saving    = ref(false)
const saved     = ref(false)
const saveError = ref('')

// ── Dirty tracking ────────────────────────────────────────────────────────────
const originalState = ref('')
function stateSnapshot() {
  return JSON.stringify({ order: order.value, vc: variantConfig.value })
}
const isDirty = computed(() => stateSnapshot() !== originalState.value)

// ── Unsaved changes confirm modal ─────────────────────────────────────────────
const confirmVisible = ref(false)
let _pendingNavNext: ((v?: boolean | string) => void) | null = null

function confirmStay() {
  confirmVisible.value = false
  _pendingNavNext?.(false)
  _pendingNavNext = null
}
async function confirmDoSave() {
  confirmVisible.value = false
  await save()
  _pendingNavNext?.()
  _pendingNavNext = null
}
function confirmDiscard() {
  confirmVisible.value = false
  _pendingNavNext?.()
  _pendingNavNext = null
}

onBeforeRouteLeave((_, __, next) => {
  if (!isDirty.value) { next(); return }
  _pendingNavNext = next
  confirmVisible.value = true
})

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

// ── Variant reorder ───────────────────────────────────────────────────────────
function moveVariantUp(src: string, vi: number) {
  if (vi === 0) return
  const arr = [...variantConfig.value[src]];
  [arr[vi - 1], arr[vi]] = [arr[vi], arr[vi - 1]]
  variantConfig.value = { ...variantConfig.value, [src]: arr }
}
function moveVariantDown(src: string, vi: number) {
  const arr = variantConfig.value[src] || []
  if (vi >= arr.length - 1) return
  const narr = [...arr];
  [narr[vi], narr[vi + 1]] = [narr[vi + 1], narr[vi]]
  variantConfig.value = { ...variantConfig.value, [src]: narr }
}

// ── Type reorder within a variant ─────────────────────────────────────────────
function moveTypeUp(src: string, vi: number, ti: number) {
  if (ti === 0) return
  const variants = variantConfig.value[src].map((v, idx) => {
    if (idx !== vi) return v
    const types = [...v.types];
    [types[ti - 1], types[ti]] = [types[ti], types[ti - 1]]
    return { ...v, types }
  })
  variantConfig.value = { ...variantConfig.value, [src]: variants }
}
function moveTypeDown(src: string, vi: number, ti: number) {
  const variant = variantConfig.value[src]?.[vi]
  if (!variant || ti >= variant.types.length - 1) return
  const variants = variantConfig.value[src].map((v, idx) => {
    if (idx !== vi) return v
    const types = [...v.types];
    [types[ti], types[ti + 1]] = [types[ti + 1], types[ti]]
    return { ...v, types }
  })
  variantConfig.value = { ...variantConfig.value, [src]: variants }
}

// ── Save ──────────────────────────────────────────────────────────────────────
async function save() {
  saving.value = true
  saveError.value = ''
  saved.value = false
  try {
    // Convert UI model → backend format
    const backendSvc: Record<string, unknown[]> = {}
    for (const src of BUILTINS) {
      backendSvc[src] = (variantConfig.value[src] || []).map(toBackendVariant)
    }
    await saveSettings({
      _section: 'sources',
      source_order_json: JSON.stringify(order.value),
      source_variant_config_json: JSON.stringify(backendSvc),
    })
    originalState.value = stateSnapshot()
    saved.value = true
    setTimeout(() => { saved.value = false }, 2500)
  } catch (e: unknown) {
    saveError.value = String(e)
  } finally {
    saving.value = false
  }
}

// ── Load ──────────────────────────────────────────────────────────────────────
async function loadConfig() {
  try {
    const cfg = await getConfig()

    // source order
    const savedOrder = [...((cfg.source_order as string[] | undefined) || [])]
      .filter(name => BUILTINS.includes(name))
    const missing = BUILTINS.filter(b => !savedOrder.includes(b))
    order.value = [...savedOrder, ...missing]

    // variant config
    const rawSvc = (cfg.source_variant_config as Record<string, unknown[]> | undefined) || {}
    const vc: Record<string, VariantConfig[]> = {}
    for (const src of BUILTINS) {
      const raw = rawSvc[src]
      if (Array.isArray(raw) && raw.length) {
        vc[src] = raw.map(v => fromBackendVariant(v as Record<string, unknown>))
      } else {
        vc[src] = defaultVariants()
      }
    }
    variantConfig.value = vc

    originalState.value = stateSnapshot()
  } catch {
    order.value = [...BUILTINS]
    const vc: Record<string, VariantConfig[]> = {}
    for (const src of BUILTINS) vc[src] = defaultVariants()
    variantConfig.value = vc
    originalState.value = stateSnapshot()
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.src-list { display: flex; flex-direction: column; gap: 10px; align-items: flex-start; }

.src-row {
  width: fit-content; min-width: 480px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); overflow: hidden; transition: border-color .12s;
}
.src-row:hover { border-color: var(--border-2); }
.src-row.drag-over { border-color: var(--teal); box-shadow: 0 0 0 2px rgba(94,224,189,.15); }

/* Source header */
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

/* Variant section */
.src-variants {
  border-top: 1px solid var(--border); background: var(--bg-2);
  padding: 14px 16px;
  display: flex; gap: 10px; flex-wrap: wrap;
}

/* Variant card */
.variant-card {
  flex: 1; min-width: 260px; max-width: 380px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; overflow: hidden;
}

.variant-hd {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px;
  background: var(--surface2); border-bottom: 1px solid var(--border);
}
.variant-rank {
  font-family: var(--font-mono); font-size: 10px; color: var(--text-3);
  width: 14px; text-align: center; flex-shrink: 0;
}
.variant-name { font-weight: 600; font-size: 13px; flex: 1; }
.variant-mv-btns { display: flex; gap: 3px; }
.icon-mini.xs { width: 20px; height: 20px; }

/* Type rows */
.type-rows { display: flex; flex-direction: column; }

.type-row {
  display: flex; align-items: center; gap: 9px;
  padding: 7px 10px;
  border-bottom: 1px solid var(--border);
  transition: background .1s;
}
.type-row:last-child { border-bottom: none; }
.type-row.type-enabled { background: rgba(94,224,189,.04); }

.type-badge {
  display: inline-block; flex-shrink: 0;
  width: 56px; text-align: center;
  padding: 2px 0; border-radius: 5px;
  font: 600 10.5px/1.4 var(--font-mono); letter-spacing: .04em;
  white-space: nowrap;
}
.type-badge.strm   { background: rgba(94,224,189,.12); color: var(--teal); }
.type-badge.hls_dl { background: rgba(245,166,35,.12);  color: var(--accent); }

.type-check { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.check-lbl  { font-size: 12px; color: var(--text); }

.type-mv-btns { display: flex; gap: 2px; margin-left: auto; }
</style>
