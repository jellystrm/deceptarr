from __future__ import annotations

import html
import json

from backend.infrastructure.config import Settings
from .cards import _attr
from .styles import CSS
from .panes import indexer_pane, download_pane
from .sources_panel import sources_panel
from .settings_panel import settings_panel
from .test_panel import test_panel

_APP_JS = r"""
(function () {
  var INTERVAL = 5000;
  var PIPELINE_TABS = ['linkgrabber', 'downloads'];
  var ALL_TABS = ['linkgrabber', 'downloads', 'sources', 'settings', 'test'];

  function openPkgIds() {
    var ids = [];
    document.querySelectorAll('.jd-tree-arr').forEach(function (a) {
      if (a.textContent.trim() === '▼') ids.push(a.id);
    });
    return ids;
  }
  function restorePkgIds(ids) {
    ids.forEach(function (arrowId) {
      var a = document.getElementById(arrowId);
      if (a && a.textContent.trim() === '▶') {
        window.jdTogglePkg(arrowId.slice(7));
      }
    });
  }

  window.jdSwitchTab = function (tab) {
    document.querySelectorAll('.jd-tab').forEach(function (t) {
      t.classList.toggle('active', t.dataset.tab === tab);
    });
    ALL_TABS.forEach(function (t) {
      var p = document.getElementById('jd-' + t);
      if (p) p.style.display = t === tab ? '' : 'none';
    });
    var isPipeline = PIPELINE_TABS.indexOf(tab) >= 0;
    var toolbar = document.getElementById('jd-main-toolbar');
    if (toolbar) toolbar.style.visibility = isPipeline ? '' : 'hidden';
    PIPELINE_TABS.forEach(function (t) {
      var sb = document.getElementById('jd-sb-' + t);
      if (sb) sb.style.display = t === tab ? '' : 'none';
    });
    history.replaceState(null, '', '/?tab=' + tab);
  };

  window.jdTogglePkg = function (id) {
    var arrow = document.getElementById('jd-arr-' + id);
    if (!arrow) return;
    var opening = arrow.textContent.trim() === '▶';
    arrow.textContent = opening ? '▼' : '▶';
    document.querySelectorAll('.jd-c-' + id).forEach(function (r) {
      r.style.display = opening ? '' : 'none';
    });
  };

  function refresh() {
    var pkgs = openPkgIds();
    fetch('/', {cache: 'no-store'})
      .then(function (r) { return r.text(); })
      .then(function (text) {
        var tmp = document.createElement('div');
        tmp.innerHTML = text;
        // Only update pipeline panes — never touch Sources/Settings/Test (would reset forms)
        ['jd-linkgrabber', 'jd-downloads', 'jd-sb-linkgrabber', 'jd-sb-downloads'].forEach(function (id) {
          var n = tmp.querySelector('#' + id);
          var o = document.getElementById(id);
          if (n && o) o.innerHTML = n.innerHTML;
        });
        PIPELINE_TABS.forEach(function (t) {
          var nb = tmp.querySelector('.jd-tab[data-tab="' + t + '"] .jd-badge');
          var ob = document.querySelector('.jd-tab[data-tab="' + t + '"] .jd-badge');
          if (nb && ob) ob.textContent = nb.textContent;
        });
        restorePkgIds(pkgs);
      })
      .catch(function () {});
  }

  window.refresh = refresh;
  setInterval(refresh, INTERVAL);

  document.addEventListener('submit', function (e) {
    if (!e.target.classList.contains('task-actions')) return;
    e.preventDefault();
    fetch(e.target.action, {method: 'POST', body: new FormData(e.target)})
      .catch(function () {})
      .finally(function () { refresh(); });
  });

  window.jdBulkAction = function (action) {
    fetch('/tasks/bulk', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'action=' + encodeURIComponent(action)
    }).catch(function () {}).finally(function () { refresh(); });
  };

  var initTab = (new URLSearchParams(window.location.search)).get('tab') || 'downloads';
  window.jdSwitchTab(initTab);
})();
"""


def render_page(settings: Settings, message: str, tab: str = "downloads", stab: str = "") -> str:
    config = settings.to_config_dict()
    templates = json.dumps(config["hls_template_sources"], indent=2)
    source_order = ",".join(config["source_order"])
    ffmpeg_args = ",".join(config["ffmpeg_extra_args"])

    lg_html, lg_pkgs, lg_links, lg_errors = indexer_pane(settings)
    dl_html, dl_pkgs, dl_running, dl_errors = download_pane(settings)
    src_html = sources_panel(config, templates, source_order)
    stg_html = settings_panel(config, ffmpeg_args, stab)
    tst_html = test_panel(config)

    msg_html = f'<div class="notice" style="margin-bottom:16px">{html.escape(message)}</div>' if message else ""

    lg_statusbar = (
        f"<span class='jd-stat'>Package(s): <span class='jd-stat-val'>{lg_pkgs}</span></span>"
        f"<span class='jd-stat'>Link(s): <span class='jd-stat-val'>{lg_links}</span></span>"
        f"<span class='jd-stat'>Online: <span class='jd-stat-val' style='color:var(--green)'>{lg_pkgs - lg_errors}</span></span>"
        f"<span class='jd-stat'>Offline: <span class='jd-stat-val' style='color:#e06c75'>{lg_errors}</span></span>"
    )
    dl_statusbar = (
        f"<span class='jd-stat'>Package(s): <span class='jd-stat-val'>{dl_pkgs}</span></span>"
        f"<span class='jd-stat'>Running: <span class='jd-stat-val' style='color:var(--green)'>{dl_running}</span></span>"
        f"<span class='jd-stat'>Errors: <span class='jd-stat-val' style='color:#e06c75'>{dl_errors}</span></span>"
    )

    VALID_TABS = {"linkgrabber", "downloads", "sources", "settings", "test"}
    active = tab if tab in VALID_TABS else "downloads"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Deceptarr</title>
  <style>{CSS}</style>
</head>
<body>
<div class="jd-wrap">

  <div class="jd-brand">
    <div class="brand-icon">D</div>
    <span class="brand-name">Deceptarr</span>
    <span class="brand-sub">{html.escape(settings.config_path)}</span>
  </div>

  <div class="jd-toolbar" id="jd-main-toolbar">
    <button class="jd-tb-btn" onclick='jdBulkAction("resume_all")'>&#9654; Start All</button>
    <button class="jd-tb-btn" onclick='jdBulkAction("pause_all")'>&#9646;&#9646; Pause All</button>
    <div class="jd-tb-sep"></div>
    <button class="jd-tb-btn" onclick='jdBulkAction("clear_done")'>&#10005; Clear Done</button>
    <div class="jd-tb-sep"></div>
    <button class="jd-tb-btn" onclick='window.refresh()' style="margin-left:auto">&#8635; Refresh</button>
  </div>

  <div class="jd-tabbar">
    <div class="jd-tab" data-tab="linkgrabber" onclick='jdSwitchTab("linkgrabber")'>&#128279; LinkGrabber <span class="jd-badge">{lg_pkgs}</span></div>
    <div class="jd-tab" data-tab="downloads" onclick='jdSwitchTab("downloads")'>&#11015; Downloads <span class="jd-badge">{dl_pkgs}</span></div>
    <div class="jd-tab" data-tab="sources" onclick='jdSwitchTab("sources")'>&#9733; Sources</div>
    <div class="jd-tab" data-tab="settings" onclick='jdSwitchTab("settings")'>&#9881; Settings</div>
    <div class="jd-tab" data-tab="test" onclick='jdSwitchTab("test")'>&#128300; Test</div>
  </div>

  <div id="jd-linkgrabber" class="jd-pane">{lg_html}</div>
  <div id="jd-downloads" class="jd-pane">{dl_html}</div>
  <div id="jd-sources" class="jd-pane" style="overflow-y:auto">
    <div style="padding:24px 28px 48px;max-width:980px;margin:0 auto">
      {''.join([msg_html, src_html]) if active == 'sources' else src_html}
    </div>
  </div>
  <div id="jd-settings" class="jd-pane" style="overflow-y:auto">
    <div style="padding:24px 28px 48px;max-width:980px;margin:0 auto">
      {''.join([msg_html, stg_html]) if active == 'settings' else stg_html}
    </div>
  </div>
  <div id="jd-test" class="jd-pane" style="overflow-y:auto">
    <div style="padding:24px 28px 48px;max-width:980px;margin:0 auto">
      {tst_html}
    </div>
  </div>

  <div id="jd-sb-linkgrabber" class="jd-statusbar"><div class="jd-sb-row">{lg_statusbar}</div></div>
  <div id="jd-sb-downloads" class="jd-statusbar"><div class="jd-sb-row">{dl_statusbar}</div></div>

</div>
<script>{_APP_JS}</script>
</body>
</html>"""
