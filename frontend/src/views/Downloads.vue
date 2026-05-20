<template>
  <div>
    <div class="page-head">
      <div>
        <h1>Downloads</h1>
        <p class="sub">Active and queued tasks. Progress, status and on-disk path live here.</p>
      </div>
      <div style="display:flex;gap:8px;align-items:center">
        <button class="btn" @click="load">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          Refresh
        </button>
      </div>
    </div>

    <div class="toolbar">
      <div class="group">
        <button class="btn" @click="bulk('resume_all')">
          <svg viewBox="0 0 24 24" fill="var(--green)" stroke="none"><polygon points="6 4 20 12 6 20"/></svg>
          Resume all
        </button>
        <button class="btn" @click="bulk('pause_all')">
          <svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>
          Pause all
        </button>
        <button class="btn" @click="bulk('clear_done')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          Clear done
        </button>
      </div>
      <div class="divider"></div>
      <div class="group">
        <span class="filter-tag">All <b>{{ jobs.length }}</b></span>
        <span class="filter-tag green-v">Running <b>{{ counts.running }}</b></span>
        <span class="filter-tag red-v">Errors <b>{{ counts.error }}</b></span>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!jobs.length" class="empty-state">
      <h3>No download tasks yet</h3>
      <p>When a source resolves to a stream, it shows up here with live progress and status.</p>
    </div>

    <!-- Table -->
    <div v-else class="card">
      <table class="table">
        <thead>
          <tr>
            <th>Title</th>
            <th style="width:260px">Progress</th>
            <th>Mode</th>
            <th>Status</th>
            <th style="width:80px"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="j in jobs" :key="j.id">
            <td>
              <div class="row-flex">
                <div class="thumb">{{ j.kind === 'movie' ? '🎬' : '📺' }}</div>
                <div>
                  <div class="row-title">
                    {{ j.title }}
                    <span v-if="j.kind === 'episode' && j.season" class="ep-tag">
                      S{{ String(j.season).padStart(2,'0') }}E{{ String(j.episode ?? 0).padStart(2,'0') }}
                    </span>
                  </div>
                  <div v-if="j.error" class="row-sub" style="color:var(--red)">{{ j.error }}</div>
                  <div v-else-if="j.save_path && j.status === 'completed'" class="row-sub" style="color:var(--green)">
                    Done · {{ j.save_path }}
                  </div>
                </div>
              </div>
            </td>
            <td>
              <div :class="['prog', progColor(j.status)]">
                <div class="prog-bar"><span :style="{ width: (j.progress * 100).toFixed(0) + '%' }"></span></div>
                <div class="prog-meta">
                  <span class="a">{{ (j.progress * 100).toFixed(0) }}%</span>
                  <span>{{ j.status }}</span>
                </div>
              </div>
            </td>
            <td>
              <span class="pill gray" style="font-family:var(--font-mono);font-size:10px">{{ j.output_mode }}</span>
            </td>
            <td>
              <span :class="['pill', statusPill(j.status)]">{{ j.status }}</span>
            </td>
            <td class="right" style="white-space:nowrap">
              <button
                v-if="j.status === 'paused' || j.status === 'error' || j.status === 'queued'"
                class="icon-mini" title="Resume"
                @click="act('resume', j.id)"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 4 20 12 6 20"/></svg>
              </button>
              <button
                v-if="j.status === 'running' || j.status === 'queued'"
                class="icon-mini" title="Pause"
                @click="act('pause', j.id)"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>
              </button>
              <button class="icon-mini danger" title="Delete" @click="act('delete', j.id)">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="card-foot">
        <span style="font-size:12.5px;color:var(--text-3)">
          {{ jobs.length }} tasks · {{ counts.running }} running · {{ counts.error }} errors · {{ counts.completed }} done
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getPipeline, jobAction, bulkAction, type PipelineJob } from '../api'

const jobs = ref<PipelineJob[]>([])
let timer: ReturnType<typeof setInterval>

const counts = computed(() => ({
  running:   jobs.value.filter(j => j.status === 'running').length,
  error:     jobs.value.filter(j => j.status === 'error').length,
  completed: jobs.value.filter(j => j.status === 'completed').length,
}))

async function load() {
  try { jobs.value = await getPipeline() } catch {}
}

async function act(action: 'resume' | 'pause' | 'delete', id: string) {
  await jobAction(action, id)
  await load()
}

async function bulk(action: 'resume_all' | 'pause_all' | 'clear_done') {
  await bulkAction(action)
  await load()
}

function statusPill(status: string) {
  if (status === 'running')   return 'green'
  if (status === 'completed') return 'teal'
  if (status === 'error')     return 'red'
  if (status === 'paused')    return 'amber'
  return 'gray'
}

function progColor(status: string) {
  if (status === 'error')  return 'red'
  if (status === 'paused') return 'amber'
  if (status === 'completed') return ''
  return ''
}

onMounted(() => { load(); timer = setInterval(load, 5000) })
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.ep-tag {
  font-size: 10px; font-family: var(--font-mono);
  background: var(--border); border-radius: 4px;
  padding: 1px 5px; margin-left: 5px; color: var(--text-3);
}
.filter-tag {
  font-size: 12px; color: var(--text-3); padding: 2px 8px;
}
.filter-tag b { font-weight: 600; color: var(--text-2); margin-left: 3px; }
.filter-tag.green-v b { color: var(--green); }
.filter-tag.red-v b   { color: var(--red); }
</style>
