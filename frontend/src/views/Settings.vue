<template>
  <div>
    <div class="page-head">
      <div>
        <h1>Settings</h1>
        <p class="sub">Connections to your *arr stack, Jellyfin, and the local worker queue.</p>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn primary" @click="save" :disabled="saving">
          {{ saving ? 'Saving…' : 'Save changes' }}
        </button>
      </div>
    </div>

    <!-- Horizontal subnav -->
    <div class="subnav">
      <button v-for="s in sections" :key="s.id" :class="{ active: active === s.id }" @click="active = s.id">
        <svg v-if="s.icon === 'radarr'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2v20M2 12h20"/></svg>
        <svg v-else-if="s.icon === 'sonarr'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="15" rx="2"/><polyline points="17 2 12 7 7 2"/></svg>
        <svg v-else-if="s.icon === 'worker'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
        <svg v-else-if="s.icon === 'tasks'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        <svg v-else-if="s.icon === 'output'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        <svg v-else-if="s.icon === 'indexer'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <svg v-else-if="s.icon === 'dlclient'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        <svg v-else-if="s.icon === 'jellyfin'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 3 21 18 3 18 12 3"/></svg>
        {{ s.label }}
      </button>
    </div>

    <!-- ── Radarr ── -->
    <div v-if="active === 'radarr'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2v20M2 12h20"/></svg>
        </div>
        <div>
          <h3>Radarr</h3>
          <p class="desc">Movie manager — connection and polling cadence.</p>
        </div>
      </div>
      <div class="fcard-body">
        <div class="form">
          <div class="field">
            <label>URL <span class="hint">required</span></label>
            <input class="input mono" v-model="cfg.radarr_url" placeholder="http://radarr:7878" />
          </div>
          <div class="field">
            <label>API Key <span class="hint">required</span></label>
            <input class="input mono" v-model="cfg.radarr_api_key" type="password" placeholder="••••••••••••••••" />
          </div>
          <div class="field full">
            <label class="check">
              <input type="checkbox" v-model="cfg.movie_enabled" />
              <span class="check-box"></span>
              <span>Poll movies <span style="color:var(--text-3);font-weight:400">— automatically pull new wanted titles on a schedule</span></span>
            </label>
          </div>
          <div class="field">
            <label>Poll interval <span class="hint">seconds</span></label>
            <input class="input mono" v-model.number="cfg.poll_interval_seconds" type="number" />
          </div>
          <div class="field">
            <label>Max items per poll <span class="hint">batch size</span></label>
            <input class="input mono" v-model.number="cfg.max_items_per_poll" type="number" />
          </div>
          <div class="field full">
            <label>Movie .strm root <span class="hint">auto-detected from Radarr root folder</span></label>
            <input class="input mono" v-model="cfg.movie_strm_root" placeholder="/movies" />
            <p class="hint-text">Leave blank to auto-detect from Radarr root folder on each start.</p>
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved" style="font-size:12px;color:var(--green)">✓ Saved</span>
        <span v-if="saveError" style="font-size:12px;color:var(--red)">{{ saveError }}</span>
        <div style="margin-left:auto;display:flex;gap:8px">
          <button class="btn primary sm" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
        </div>
      </div>
    </div>

    <!-- ── Sonarr ── -->
    <div v-else-if="active === 'sonarr'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="15" rx="2"/><polyline points="17 2 12 7 7 2"/></svg>
        </div>
        <div>
          <h3>Sonarr</h3>
          <p class="desc">TV series manager — connection and polling cadence.</p>
        </div>
      </div>
      <div class="fcard-body">
        <div class="form">
          <div class="field">
            <label>URL <span class="hint">required</span></label>
            <input class="input mono" v-model="cfg.sonarr_url" placeholder="http://sonarr:8989" />
          </div>
          <div class="field">
            <label>API Key <span class="hint">required</span></label>
            <input class="input mono" v-model="cfg.sonarr_api_key" type="password" placeholder="••••••••••••••••" />
          </div>
          <div class="field full">
            <label class="check">
              <input type="checkbox" v-model="cfg.series_enabled" />
              <span class="check-box"></span>
              <span>Poll series <span style="color:var(--text-3);font-weight:400">— automatically pull new wanted episodes on a schedule</span></span>
            </label>
          </div>
          <div class="field">
            <label>Poll interval <span class="hint">seconds</span></label>
            <input class="input mono" v-model.number="cfg.poll_interval_seconds" type="number" />
          </div>
          <div class="field">
            <label>Max items per poll <span class="hint">batch size</span></label>
            <input class="input mono" v-model.number="cfg.max_items_per_poll" type="number" />
          </div>
          <div class="field full">
            <label>Series .strm root <span class="hint">auto-detected from Sonarr root folder</span></label>
            <input class="input mono" v-model="cfg.series_strm_root" placeholder="/series" />
            <p class="hint-text">Leave blank to auto-detect from Sonarr root folder on each start.</p>
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved" style="font-size:12px;color:var(--green)">✓ Saved</span>
        <span v-if="saveError" style="font-size:12px;color:var(--red)">{{ saveError }}</span>
        <div style="margin-left:auto"><button class="btn primary sm" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button></div>
      </div>
    </div>

    <!-- ── Worker ── -->
    <div v-else-if="active === 'worker'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
        </div>
        <div>
          <h3>Worker</h3>
          <p class="desc">Concurrency and retry behaviour for the local task queue.</p>
        </div>
      </div>
      <div class="fcard-body">
        <div class="form">
          <div class="field full">
            <label class="check">
              <input type="checkbox" v-model="cfg.worker_enabled" />
              <span class="check-box"></span>
              <span>Worker enabled</span>
            </label>
          </div>
          <div class="field">
            <label>Retry after <span class="hint">seconds</span></label>
            <input class="input mono" v-model.number="cfg.retry_after_seconds" type="number" />
          </div>
          <div class="field">
            <label>Job detail retention <span class="hint">hours</span></label>
            <input class="input mono" v-model.number="cfg.job_detail_retention_hours" type="number" />
          </div>
          <div class="field full">
            <label>State path</label>
            <input class="input mono" v-model="cfg.state_path" />
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved" style="font-size:12px;color:var(--green)">✓ Saved</span>
        <span v-if="saveError" style="font-size:12px;color:var(--red)">{{ saveError }}</span>
        <div style="margin-left:auto"><button class="btn primary sm" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button></div>
      </div>
    </div>

    <!-- ── Tasks (TMDB) ── -->
    <div v-else-if="active === 'tasks'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        </div>
        <div>
          <h3>TMDB</h3>
          <p class="desc">API key for title and year resolution in source queries.</p>
        </div>
      </div>
      <div class="fcard-body">
        <div class="form">
          <div class="field full">
            <label>TMDB API Key <span class="hint">get free key at themoviedb.org</span></label>
            <input class="input mono" v-model="cfg.tmdb_api_key" type="password" placeholder="••••••••••••••••••••••••••••••••" />
            <p class="hint-text">Required for title/year resolution in source queries. Free at <a href="https://www.themoviedb.org/settings/api" target="_blank">themoviedb.org</a>.</p>
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved" style="font-size:12px;color:var(--green)">✓ Saved</span>
        <span v-if="saveError" style="font-size:12px;color:var(--red)">{{ saveError }}</span>
        <div style="margin-left:auto"><button class="btn primary sm" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button></div>
      </div>
    </div>

    <!-- ── Output / Runtime ── -->
    <div v-else-if="active === 'output'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        </div>
        <div>
          <h3>Output</h3>
          <p class="desc">Where finished files land and how they are handled.</p>
        </div>
      </div>
      <div class="fcard-body">
        <div class="form">
          <div class="field">
            <label>Default Output Mode</label>
            <select class="select" v-model="cfg.default_output_mode">
              <option value="strm">strm — write .strm file (recommended)</option>
              <option value="hls-dl">hls-dl — download HLS to file</option>
            </select>
          </div>
          <div class="field">
            <label>Download Container</label>
            <select class="select" v-model="cfg.download_container">
              <option value="mkv">mkv</option>
              <option value="mp4">mp4</option>
              <option value="ts">ts</option>
            </select>
          </div>
          <div class="field">
            <label>Import Mode <span class="hint">Radarr/Sonarr</span></label>
            <select class="select" v-model="cfg.import_mode">
              <option value="Move">Move</option>
              <option value="Copy">Copy</option>
              <option value="Hardlink">Hardlink</option>
            </select>
          </div>
          <div class="field">
            <label>Log Level</label>
            <select class="select" v-model="cfg.log_level">
              <option>DEBUG</option><option>INFO</option><option>WARNING</option><option>ERROR</option>
            </select>
          </div>
          <div class="field full">
            <label class="check">
              <input type="checkbox" v-model="cfg.expose_both_modes" />
              <span class="check-box"></span>
              <span>Expose both modes in Torznab results</span>
            </label>
          </div>
          <div class="field">
            <label>ffmpeg path</label>
            <input class="input mono" v-model="cfg.ffmpeg_path" placeholder="ffmpeg" />
          </div>
          <div class="field">
            <label>ffmpeg extra args <span class="hint">comma-separated</span></label>
            <input class="input mono" v-model="ffmpegArgs" placeholder="-c:v copy, -c:a aac" />
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved" style="font-size:12px;color:var(--green)">✓ Saved</span>
        <span v-if="saveError" style="font-size:12px;color:var(--red)">{{ saveError }}</span>
        <div style="margin-left:auto"><button class="btn primary sm" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button></div>
      </div>
    </div>

    <!-- ── Indexer ── -->
    <div v-else-if="active === 'indexer'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </div>
        <div>
          <h3>Torznab Indexer</h3>
          <p class="desc">Configure the Torznab API — paste the key into Radarr / Sonarr → Indexers.</p>
        </div>
      </div>
      <div class="fcard-body">
        <div class="form">
          <div class="field full">
            <label>API Key</label>
            <div class="input-group">
              <input class="input mono" :value="cfg.torznab_api_key" readonly style="cursor:default" />
              <button class="btn" :class="{ 'key-copied': keyCopied }" title="Copy" @click="copyKey">
                {{ keyCopied ? '✓ Copied' : '⎘ Copy' }}
              </button>
              <button class="btn danger" title="Regenerate" :disabled="keyRegen" @click="regenKey">↻</button>
            </div>
            <p class="hint-text">Paste this key into Radarr / Sonarr → Settings → Indexers → Torznab.</p>
          </div>
          <div class="field full">
            <label>Public Base URL</label>
            <input class="input mono" v-model="cfg.public_base_url" placeholder="http://deceptarr:8765" />
          </div>
          <div class="field full">
            <label>Server Labels <span class="hint">comma-separated</span></label>
            <input class="input mono" v-model="serverLabels" placeholder="ViệtSub, Lồng Tiếng" />
          </div>
          <div class="field full">
            <label class="check">
              <input type="checkbox" v-model="cfg.torznab_group_sources" />
              <span class="check-box"></span>
              <span>Group results by source</span>
            </label>
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved" style="font-size:12px;color:var(--green)">✓ Saved</span>
        <span v-if="saveError" style="font-size:12px;color:var(--red)">{{ saveError }}</span>
        <div style="margin-left:auto"><button class="btn primary sm" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button></div>
      </div>
    </div>

    <!-- ── Download Client ── -->
    <div v-else-if="active === 'dlclient'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        </div>
        <div>
          <h3>Download Client</h3>
          <p class="desc">qBittorrent connection and download root path.</p>
        </div>
      </div>
      <div class="fcard-body">
        <div class="form">
          <div class="field">
            <label>UI Host</label>
            <input class="input mono" v-model="cfg.ui_host" />
          </div>
          <div class="field">
            <label>UI Port</label>
            <input class="input mono" v-model.number="cfg.ui_port" type="number" />
          </div>
          <div class="field">
            <label>qBittorrent Username</label>
            <input class="input" v-model="cfg.qb_username" />
          </div>
          <div class="field">
            <label>qBittorrent Password</label>
            <input class="input" v-model="cfg.qb_password" type="password" />
          </div>
          <div class="field full">
            <label>Download Root <span class="hint">auto-detected from qBittorrent savePath</span></label>
            <input class="input mono" v-model="cfg.download_root" placeholder="/downloads" />
            <p class="hint-text">Leave blank to auto-detect from Radarr/Sonarr download client on each start.</p>
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved" style="font-size:12px;color:var(--green)">✓ Saved</span>
        <span v-if="saveError" style="font-size:12px;color:var(--red)">{{ saveError }}</span>
        <div style="margin-left:auto"><button class="btn primary sm" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button></div>
      </div>
    </div>

    <!-- ── Jellyfin ── -->
    <div v-else-if="active === 'jellyfin'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 3 21 18 3 18 12 3"/></svg>
        </div>
        <div>
          <h3>Jellyfin</h3>
          <p class="desc">Library refresh + playback integration.</p>
        </div>
      </div>
      <div class="fcard-body">
        <div class="form">
          <div class="field">
            <label>URL</label>
            <input class="input mono" v-model="cfg.jellyfin_url" placeholder="http://jellyfin:8096" />
          </div>
          <div class="field">
            <label>API Key</label>
            <input class="input mono" v-model="cfg.jellyfin_api_key" type="password" placeholder="••••••••••••••••" />
          </div>
          <div class="field full">
            <label class="check">
              <input type="checkbox" v-model="cfg.jellyfin_scan_after_strm" />
              <span class="check-box"></span>
              <span>Trigger library scan after .strm write</span>
            </label>
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved" style="font-size:12px;color:var(--green)">✓ Saved</span>
        <span v-if="saveError" style="font-size:12px;color:var(--red)">{{ saveError }}</span>
        <div style="margin-left:auto"><button class="btn primary sm" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getConfig, saveSettings, type Config } from '../api'

// Map frontend section ID → backend _section name
const sectionBackendId: Record<string, string> = {
  output:   'runtime',
  dlclient: 'downloader',
}

const sections = [
  { id: 'radarr',   label: 'Radarr',          icon: 'radarr' },
  { id: 'sonarr',   label: 'Sonarr',          icon: 'sonarr' },
  { id: 'worker',   label: 'Worker',          icon: 'worker' },
  { id: 'tasks',    label: 'TMDB',            icon: 'tasks'  },
  { id: 'output',   label: 'Output',          icon: 'output' },
  { id: 'indexer',  label: 'Indexer',         icon: 'indexer' },
  { id: 'dlclient', label: 'Download Client', icon: 'dlclient' },
  { id: 'jellyfin', label: 'Jellyfin',        icon: 'jellyfin' },
]

const active   = ref('radarr')
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const cfg      = ref<Record<string, any>>({})
const saving   = ref(false)
const saved    = ref(false)
const saveError = ref('')
const keyCopied = ref(false)
const keyRegen  = ref(false)

async function copyKey() {
  try {
    await navigator.clipboard.writeText(String(cfg.value.torznab_api_key || ''))
    keyCopied.value = true
    setTimeout(() => { keyCopied.value = false }, 1800)
  } catch {}
}

async function regenKey() {
  keyRegen.value = true
  try {
    const res = await fetch('/api/regen-torznab-key', { method: 'POST' })
    const data = await res.json()
    cfg.value.torznab_api_key = data.torznab_api_key
  } catch {}
  finally { keyRegen.value = false }
}

const ffmpegArgs = computed({
  get: () => ((cfg.value.ffmpeg_extra_args as string[]) || []).join(', '),
  set: (v: string) => { cfg.value.ffmpeg_extra_args = v.split(',').map((s: string) => s.trim()).filter(Boolean) },
})
const serverLabels = computed({
  get: () => ((cfg.value.server_labels as string[]) || []).join(', '),
  set: (v: string) => { cfg.value.server_labels = v.split(',').map((s: string) => s.trim()).filter(Boolean) },
})

async function save() {
  saving.value = true
  saveError.value = ''
  saved.value = false
  try {
    const backendSection = sectionBackendId[active.value] || active.value
    const payload: Record<string, unknown> = { _section: backendSection, ...cfg.value }
    if (active.value === 'output')  payload.ffmpeg_extra_args = ffmpegArgs.value
    if (active.value === 'indexer') payload.server_labels     = serverLabels.value
    await saveSettings(payload)
    saved.value = true
    setTimeout(() => { saved.value = false }, 2500)
  } catch (e: unknown) {
    saveError.value = String(e)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try { cfg.value = await getConfig() as Record<string, any> } catch {}
})
</script>

<style scoped>
.fcard-foot {
  padding: 14px 22px; border-top: 1px solid var(--border);
  background: var(--bg-2); display: flex; align-items: center; gap: 10px;
}
.key-copied { color: var(--green) !important; border-color: rgba(74,222,128,.3) !important; }
</style>
