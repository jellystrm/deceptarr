<template>
  <div>
    <div class="page-head">
      <div>
        <h1>Settings</h1>
        <p class="sub">Configure service connections and system behaviour.</p>
      </div>
    </div>

    <!-- Subnav -->
    <div class="subnav">
      <template v-for="s in sections" :key="s.id">
        <div v-if="s.id === 'sep'" class="subnav-sep"></div>
        <button v-else :class="{ active: active === s.id }" @click="active = s.id">
          <!-- connection icons -->
          <svg v-if="s.icon === 'radarr'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2v20M2 12h20"/></svg>
          <svg v-else-if="s.icon === 'sonarr'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="15" rx="2"/><polyline points="17 2 12 7 7 2"/></svg>
          <svg v-else-if="s.icon === 'jellyfin'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 3 21 18 3 18 12 3"/></svg>
          <svg v-else-if="s.icon === 'tmdb'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <!-- system icons -->
          <svg v-else-if="s.icon === 'schedule'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          <svg v-else-if="s.icon === 'output'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          <svg v-else-if="s.icon === 'indexer'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <svg v-else-if="s.icon === 'dlclient'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          {{ s.label }}
        </button>
      </template>
    </div>

    <!-- ── Radarr ── -->
    <div v-if="active === 'radarr'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2v20M2 12h20"/></svg></div>
        <div><h3>Radarr</h3><p class="desc">Movie manager connection settings.</p></div>
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
            <label>Movie .strm root <span class="hint">auto-detected from Radarr root folder</span></label>
            <input class="input mono" v-model="cfg.movie_strm_root" placeholder="/movies" />
            <p class="hint-text">Leave blank to auto-detect from Radarr root folder on each start.</p>
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved"     class="save-ok">✓ Saved</span>
        <span v-if="saveError" class="save-err">{{ saveError }}</span>
        <button class="btn primary" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      </div>
    </div>

    <!-- ── Sonarr ── -->
    <div v-else-if="active === 'sonarr'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="15" rx="2"/><polyline points="17 2 12 7 7 2"/></svg></div>
        <div><h3>Sonarr</h3><p class="desc">TV series manager connection settings.</p></div>
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
            <label>Series .strm root <span class="hint">auto-detected from Sonarr root folder</span></label>
            <input class="input mono" v-model="cfg.series_strm_root" placeholder="/series" />
            <p class="hint-text">Leave blank to auto-detect from Sonarr root folder on each start.</p>
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved"     class="save-ok">✓ Saved</span>
        <span v-if="saveError" class="save-err">{{ saveError }}</span>
        <button class="btn primary" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      </div>
    </div>

    <!-- ── Jellyfin ── -->
    <div v-else-if="active === 'jellyfin'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 3 21 18 3 18 12 3"/></svg></div>
        <div><h3>Jellyfin</h3><p class="desc">Library refresh + playback integration.</p></div>
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
        <span v-if="saved"     class="save-ok">✓ Saved</span>
        <span v-if="saveError" class="save-err">{{ saveError }}</span>
        <button class="btn primary" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      </div>
    </div>

    <!-- ── TMDB ── -->
    <div v-else-if="active === 'tasks'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
        <div><h3>TMDB</h3><p class="desc">API key for title and year resolution in source queries.</p></div>
      </div>
      <div class="fcard-body">
        <div class="form">
          <div class="field full">
            <label>TMDB API Key <span class="hint">get free key at themoviedb.org</span></label>
            <input class="input mono" v-model="cfg.tmdb_api_key" type="password" placeholder="••••••••••••••••••••••••••••••••" style="max-width:420px" />
            <p class="hint-text">Required for title/year resolution. Free at <a href="https://www.themoviedb.org/settings/api" target="_blank">themoviedb.org</a>.</p>
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved"     class="save-ok">✓ Saved</span>
        <span v-if="saveError" class="save-err">{{ saveError }}</span>
        <button class="btn primary" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      </div>
    </div>

    <!-- ── Schedule ── -->
    <div v-else-if="active === 'schedule'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
        <div><h3>Poll schedule</h3><p class="desc">Independent polling schedules for Radarr and Sonarr.</p></div>
      </div>
      <div class="fcard-body">
        <div class="sched-grid">

          <!-- Movies column -->
          <div class="sched-col" :class="{ 'sched-off': !cfg.movie_enabled }">
            <label class="check sched-toggle">
              <input type="checkbox" v-model="cfg.movie_enabled" />
              <span class="check-box"></span>
              <span>Movies <span class="muted">— Radarr</span></span>
            </label>
            <fieldset class="sched-fields" :disabled="!cfg.movie_enabled">
              <div class="sched-row">
                <label class="sched-label">Interval</label>
                <div style="display:flex;gap:0">
                  <input class="input mono" type="number" min="1"
                    :value="moviePollDisplay"
                    @input="setMoviePoll(($event.target as HTMLInputElement).valueAsNumber)"
                    style="border-top-right-radius:0;border-bottom-right-radius:0;border-right:0;width:72px" />
                  <select class="select" v-model="moviePollUnit"
                    style="border-top-left-radius:0;border-bottom-left-radius:0;width:110px">
                    <option value="minutes">minutes</option>
                    <option value="hours">hours</option>
                  </select>
                </div>
                <span class="sched-hint">every {{ moviePollSummary }}</span>
              </div>
              <div class="sched-row">
                <label class="sched-label">Max items</label>
                <input class="input mono" v-model.number="cfg.movie_max_items_per_poll" type="number" min="1" style="width:80px" />
                <span class="sched-hint">per poll</span>
              </div>
            </fieldset>
          </div>

          <div class="sched-divider"></div>

          <!-- Series column -->
          <div class="sched-col" :class="{ 'sched-off': !cfg.series_enabled }">
            <label class="check sched-toggle">
              <input type="checkbox" v-model="cfg.series_enabled" />
              <span class="check-box"></span>
              <span>Series <span class="muted">— Sonarr</span></span>
            </label>
            <fieldset class="sched-fields" :disabled="!cfg.series_enabled">
              <div class="sched-row">
                <label class="sched-label">Interval</label>
                <div style="display:flex;gap:0">
                  <input class="input mono" type="number" min="1"
                    :value="seriesPollDisplay"
                    @input="setSeriesPoll(($event.target as HTMLInputElement).valueAsNumber)"
                    style="border-top-right-radius:0;border-bottom-right-radius:0;border-right:0;width:72px" />
                  <select class="select" v-model="seriesPollUnit"
                    style="border-top-left-radius:0;border-bottom-left-radius:0;width:110px">
                    <option value="minutes">minutes</option>
                    <option value="hours">hours</option>
                  </select>
                </div>
                <span class="sched-hint">every {{ seriesPollSummary }}</span>
              </div>
              <div class="sched-row">
                <label class="sched-label">Max items</label>
                <input class="input mono" v-model.number="cfg.series_max_items_per_poll" type="number" min="1" style="width:80px" />
                <span class="sched-hint">per poll</span>
              </div>
            </fieldset>
          </div>

        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved"     class="save-ok">✓ Saved</span>
        <span v-if="saveError" class="save-err">{{ saveError }}</span>
        <button class="btn primary" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      </div>
    </div>

    <!-- ── Output ── -->
    <div v-else-if="active === 'output'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg></div>
        <div><h3>Output</h3><p class="desc">How Deceptarr delivers media to your library.</p></div>
      </div>
      <div class="fcard-body" style="display:flex;flex-direction:column;gap:20px">

        <!-- Type selector -->
        <div class="out-type-grid">
          <label :class="['out-type-card', { active: cfg.default_output_mode === 'strm' }]"
            @click="cfg.default_output_mode = 'strm'">
            <div class="out-type-radio">
              <span :class="['radio-dot', { on: cfg.default_output_mode === 'strm' }]"></span>
            </div>
            <div>
              <div class="out-type-name">STRM <span class="pill teal flat" style="font-size:10px;margin-left:4px">recommended</span></div>
              <div class="out-type-desc">Writes a .strm redirect file to your Jellyfin library. No download — Jellyfin streams directly from the source URL.</div>
            </div>
          </label>
          <label :class="['out-type-card', { active: cfg.default_output_mode === 'hls-dl' }]"
            @click="cfg.default_output_mode = 'hls-dl'">
            <div class="out-type-radio">
              <span :class="['radio-dot', { on: cfg.default_output_mode === 'hls-dl' }]"></span>
            </div>
            <div>
              <div class="out-type-name">HLS Download</div>
              <div class="out-type-desc">Downloads the HLS stream to a local video file via ffmpeg, then *arr imports it to your library.</div>
            </div>
          </label>
        </div>

        <!-- STRM info -->
        <div v-if="cfg.default_output_mode === 'strm'" class="out-info">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          .strm files are written directly to your library root folders (auto-detected from Radarr / Sonarr on startup). Jellyfin picks them up on next scan.
        </div>

        <!-- HLS-DL settings -->
        <template v-if="cfg.default_output_mode === 'hls-dl'">
          <div class="out-section-label">Download settings</div>
          <div class="form" style="margin:0">
            <div class="field">
              <label>Container</label>
              <select class="select" v-model="cfg.download_container">
                <option value="mkv">mkv</option>
                <option value="mp4">mp4</option>
                <option value="ts">ts (raw, no remux)</option>
              </select>
            </div>
            <div class="field">
              <label>Import mode <span class="hint">*arr → library</span></label>
              <select class="select" v-model="cfg.import_mode">
                <option value="Move">Move</option>
                <option value="Copy">Copy</option>
                <option value="Hardlink">Hardlink</option>
              </select>
              <p class="hint-text">How *arr imports the downloaded file from the downloads folder into your library.</p>
            </div>
          </div>

          <div class="out-section-label" style="display:flex;align-items:center;gap:10px">
            ffmpeg
            <span v-if="ffmpegChecking" class="ff-badge ff-checking">checking…</span>
            <span v-else-if="ffmpegStatus?.ok" class="ff-badge ff-ok">✓ {{ ffmpegStatus.version?.split(' ').slice(0,3).join(' ') }}</span>
            <span v-else-if="ffmpegStatus" class="ff-badge ff-err">✗ not found</span>
          </div>
          <div class="form" style="margin:0">
            <div class="field">
              <label>Binary path</label>
              <input class="input mono" v-model="cfg.ffmpeg_path" placeholder="ffmpeg"
                @change="recheckFfmpeg" @blur="recheckFfmpeg" />
              <p v-if="ffmpegStatus && !ffmpegStatus.ok" class="hint-text" style="color:var(--red)">
                {{ ffmpegStatus.hint }}
              </p>
              <p v-else class="hint-text">Leave blank to use <code>ffmpeg</code> from PATH.</p>
            </div>
            <div class="field">
              <label>Extra args <span class="hint">comma-separated</span></label>
              <input class="input mono" v-model="ffmpegArgs" placeholder="-c:v copy, -c:a aac" />
            </div>
          </div>
        </template>

      </div>
      <div class="fcard-foot">
        <span v-if="saved"     class="save-ok">✓ Saved</span>
        <span v-if="saveError" class="save-err">{{ saveError }}</span>
        <button class="btn primary" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      </div>
    </div>

    <!-- ── Indexer ── -->
    <div v-else-if="active === 'indexer'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></div>
        <div><h3>Torznab Indexer</h3><p class="desc">Configure the Torznab API — paste the key into Radarr / Sonarr → Indexers.</p></div>
      </div>
      <div class="fcard-body">
        <div class="form">
          <div class="field full">
            <label>API Key</label>
            <div class="key-row">
              <input class="input mono key-input" :value="cfg.torznab_api_key" readonly />
              <button class="icon-btn" :class="{ copied: keyCopied }" title="Copy key" @click="copyKey">
                <svg v-if="!keyCopied" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              </button>
              <button class="icon-btn danger" title="Regenerate key" :disabled="keyRegen" @click="regenKey">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
              </button>
            </div>
            <p v-if="keyRegenDone" class="hint-text" style="color:var(--amber)">⚠ Requires restart to take effect — update the key in Radarr / Sonarr → Indexers.</p>
            <p v-else class="hint-text">Paste into Radarr / Sonarr → Settings → Indexers → Torznab.</p>
          </div>
          <div class="field">
            <label>Public Base URL</label>
            <input class="input mono" v-model="cfg.public_base_url" placeholder="http://deceptarr:8765" />
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved"     class="save-ok">✓ Saved</span>
        <span v-if="saveError" class="save-err">{{ saveError }}</span>
        <button class="btn primary" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      </div>
    </div>

    <!-- ── Download Client ── -->
    <div v-else-if="active === 'dlclient'" class="fcard">
      <div class="fcard-head">
        <div class="fcard-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg></div>
        <div><h3>Download Client</h3><p class="desc">qBittorrent connection, paths, and queue behaviour.</p></div>
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
            <p class="hint-text">Leave blank to auto-detect on each start.</p>
          </div>
          <div class="field">
            <label>Retry failed jobs after <span class="hint">seconds</span></label>
            <input class="input mono" v-model.number="cfg.retry_after_seconds" type="number" min="0" />
            <p class="hint-text">How long to wait before retrying a failed download.</p>
          </div>
          <div class="field">
            <label>Job retention <span class="hint">hours</span></label>
            <input class="input mono" v-model.number="cfg.job_detail_retention_hours" type="number" min="1" />
            <p class="hint-text">Completed/failed jobs visible in Downloads for this long before auto-cleanup.</p>
          </div>
        </div>
      </div>
      <div class="fcard-foot">
        <span v-if="saved"     class="save-ok">✓ Saved</span>
        <span v-if="saveError" class="save-err">{{ saveError }}</span>
        <button class="btn primary" @click="save" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getConfig, saveSettings, checkFfmpeg, type FfmpegCheckResult } from '../api'

const sectionBackendId: Record<string, string> = {
  tasks:    'tasks',
  output:   'runtime',
  dlclient: 'downloader',
  schedule: 'radarr',   // poll_interval lives in radarr section on backend
}

const sections = [
  // Connections
  { id: 'radarr',   label: 'Radarr',          icon: 'radarr'   },
  { id: 'sonarr',   label: 'Sonarr',          icon: 'sonarr'   },
  { id: 'jellyfin', label: 'Jellyfin',        icon: 'jellyfin' },
  { id: 'tasks',    label: 'TMDB',            icon: 'tmdb'     },
  // separator
  { id: 'sep',      label: '',                icon: ''         },
  // System
  { id: 'schedule', label: 'Schedule',        icon: 'schedule' },
  { id: 'output',   label: 'Output',          icon: 'output'   },
  { id: 'indexer',  label: 'Indexer',         icon: 'indexer'  },
  { id: 'dlclient', label: 'Download Client', icon: 'dlclient' },
]

const active    = ref('radarr')
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const cfg       = ref<Record<string, any>>({})
const saving    = ref(false)
const saved     = ref(false)
const saveError = ref('')
const keyCopied     = ref(false)
const keyRegen      = ref(false)
const keyRegenDone  = ref(false)
const ffmpegStatus  = ref<FfmpegCheckResult | null>(null)
const ffmpegChecking = ref(false)

async function recheckFfmpeg() {
  ffmpegChecking.value = true
  try {
    ffmpegStatus.value = await checkFfmpeg(cfg.value.ffmpeg_path || '')
  } catch { ffmpegStatus.value = null }
  finally { ffmpegChecking.value = false }
}

// ── Poll interval helpers ─────────────────────────────────────────────────────
type PollUnit = 'minutes' | 'hours'

const moviePollUnit  = ref<PollUnit>('minutes')
const seriesPollUnit = ref<PollUnit>('hours')

function secsToDisplay(secs: number, unit: PollUnit) {
  return unit === 'hours' ? Math.round(secs / 3600) : Math.round(secs / 60)
}
function displayToSecs(v: number, unit: PollUnit) {
  return unit === 'hours' ? v * 3600 : v * 60
}
function secsSummary(secs: number) {
  if (secs < 3600) return `${Math.round(secs / 60)} min`
  if (secs % 3600 === 0) return `${secs / 3600}h`
  return `${Math.round(secs / 60)} min`
}

const moviePollDisplay = computed(() =>
  secsToDisplay(cfg.value.movie_poll_interval_seconds || 300, moviePollUnit.value))
const seriesPollDisplay = computed(() =>
  secsToDisplay(cfg.value.series_poll_interval_seconds || 3600, seriesPollUnit.value))

function setMoviePoll(v: number) {
  if (!Number.isFinite(v) || v < 1) return
  cfg.value.movie_poll_interval_seconds = displayToSecs(v, moviePollUnit.value)
}
function setSeriesPoll(v: number) {
  if (!Number.isFinite(v) || v < 1) return
  cfg.value.series_poll_interval_seconds = displayToSecs(v, seriesPollUnit.value)
}

const moviePollSummary  = computed(() => secsSummary(cfg.value.movie_poll_interval_seconds  || 300))
const seriesPollSummary = computed(() => secsSummary(cfg.value.series_poll_interval_seconds || 3600))

// ── ffmpeg args ───────────────────────────────────────────────────────────────
const ffmpegArgs = computed({
  get: () => ((cfg.value.ffmpeg_extra_args as string[]) || []).join(', '),
  set: (v: string) => { cfg.value.ffmpeg_extra_args = v.split(',').map((s: string) => s.trim()).filter(Boolean) },
})

// ── Actions ───────────────────────────────────────────────────────────────────
async function copyKey() {
  try {
    await navigator.clipboard.writeText(String(cfg.value.torznab_api_key || ''))
    keyCopied.value = true
    setTimeout(() => { keyCopied.value = false }, 1800)
  } catch {}
}

async function regenKey() {
  keyRegen.value = true
  keyRegenDone.value = false
  try {
    const res = await fetch('/api/regen-torznab-key', { method: 'POST' })
    const data = await res.json()
    cfg.value.torznab_api_key = data.torznab_api_key
    keyRegenDone.value = true
  } catch {}
  finally { keyRegen.value = false }
}

async function save() {
  saving.value = true
  saveError.value = ''
  saved.value = false
  try {
    const backendSection = sectionBackendId[active.value] || active.value
    const payload: Record<string, unknown> = { _section: backendSection, ...cfg.value }
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
  try {
    cfg.value = await getConfig() as Record<string, any>
    const ms = cfg.value.movie_poll_interval_seconds  || 300
    const ss = cfg.value.series_poll_interval_seconds || 3600
    moviePollUnit.value  = ms  >= 3600 && ms  % 3600 === 0 ? 'hours' : 'minutes'
    seriesPollUnit.value = ss  >= 3600 && ss  % 3600 === 0 ? 'hours' : 'minutes'
    recheckFfmpeg()
  } catch {}
})
</script>

<style scoped>
.subnav-sep {
  width: 1px; height: 20px; background: var(--border);
  margin: 0 4px; align-self: center; flex-shrink: 0;
}
/* ── API key row ── */
.key-row {
  display: flex; gap: 0; max-width: 520px;
}
.key-input {
  flex: 1; border-top-right-radius: 0; border-bottom-right-radius: 0;
  cursor: default; font-size: 13px;
}
.icon-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 38px; height: 38px; flex-shrink: 0;
  background: var(--surface-2); border: 1px solid var(--border);
  border-left: 0; color: var(--text-2);
  cursor: pointer; transition: background .12s, color .12s;
}
.key-row .icon-btn                { border-radius: 0; }
.key-row .icon-btn:last-of-type   { border-radius: 0 8px 8px 0; }
.icon-btn:hover { background: var(--surface-3); color: var(--text); }
.icon-btn.copied { color: var(--teal); }
.icon-btn.danger { color: var(--red-muted, var(--text-3)); }
.icon-btn.danger:hover { background: var(--red-soft); color: var(--red); }
.icon-btn:disabled { opacity: .4; cursor: default; pointer-events: none; }

/* ── Global input max-width in settings forms ── */
.fcard-body .input:not(.key-input),
.fcard-body .select { max-width: 480px; }
.fcard-body .input-group { max-width: 480px; }

.key-copied { color: var(--green) !important; border-color: rgba(74,222,128,.3) !important; }
.save-ok  { font-size: 12px; color: var(--green); }
.save-err { font-size: 12px; color: var(--red); }

/* ── Schedule 2-column layout ── */
.sched-grid {
  display: grid;
  grid-template-columns: 1fr 1px 1fr;
  gap: 0 28px;
}
.sched-col { display: flex; flex-direction: column; gap: 0; }
.sched-divider { background: var(--border); }

.sched-toggle { font-size: 14px; font-weight: 600; padding-bottom: 14px; border-bottom: 1px solid var(--border); margin-bottom: 14px; }
.muted { color: var(--text-3); font-weight: 400; }

.sched-fields {
  border: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 10px;
  transition: opacity .15s;
}
.sched-fields:disabled { opacity: .38; pointer-events: none; }

.sched-row { display: flex; align-items: center; gap: 10px; }
.sched-label { font-size: 12.5px; color: var(--text-3); width: 72px; flex-shrink: 0; white-space: nowrap; }
.sched-hint  { font-size: 11.5px; color: var(--text-3); }

.sched-off .sched-toggle { opacity: .7; }

/* ── Output type selector ── */
.out-type-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.out-type-card {
  display: flex; gap: 12px; align-items: flex-start;
  padding: 14px 16px; border-radius: 10px;
  border: 1.5px solid var(--border); background: var(--bg);
  cursor: pointer; transition: border-color .12s, background .12s;
}
.out-type-card:hover { border-color: var(--border-strong); }
.out-type-card.active { border-color: var(--teal); background: var(--teal-soft); }
.out-type-radio { flex-shrink: 0; margin-top: 2px; }
.radio-dot {
  width: 16px; height: 16px; border-radius: 50%;
  border: 1.5px solid var(--border-strong); display: block;
  transition: all .12s;
}
.radio-dot.on { border-color: var(--teal); border-width: 5px; background: var(--bg); }
.out-type-name { font-size: 13.5px; font-weight: 600; color: var(--text-2); margin-bottom: 4px; }
.out-type-desc { font-size: 12px; color: var(--text-3); line-height: 1.5; }

.out-info {
  display: flex; gap: 8px; align-items: flex-start;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: 8px; padding: 10px 14px;
  font-size: 12.5px; color: var(--text-3); line-height: 1.5;
}
.out-info svg { flex-shrink: 0; margin-top: 2px; color: var(--text-3); }
.out-section-label {
  font-size: 11.5px; font-weight: 600; color: var(--text-3);
  text-transform: uppercase; letter-spacing: .06em;
  padding-bottom: 8px; border-bottom: 1px solid var(--border);
}

/* ── ffmpeg status badge ── */
.ff-badge {
  font-size: 11px; font-weight: 500; padding: 2px 8px;
  border-radius: 5px; font-family: var(--font-mono);
}
.ff-checking { background: var(--surface-2); color: var(--text-3); }
.ff-ok  { background: var(--teal-soft);   color: var(--teal);   border: 1px solid var(--teal-line); }
.ff-err { background: var(--red-soft);    color: var(--red);    border: 1px solid var(--red-line); }
</style>
