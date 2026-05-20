"""Sources tab — priority-ordered source list with built-in + custom sources."""
from __future__ import annotations

import json
from typing import Any

from .cards import _attr


def sources_panel(config: dict[str, Any], templates: str, source_order: str) -> str:
    from backend.sources import BUILTIN_SOURCES, DEFAULT_SOURCE_ORDER

    sources_data = config.get("hls_template_sources", [])
    custom_names = [s.get("name", "") for s in sources_data if s.get("name")]
    configured_order = config.get("source_order", DEFAULT_SOURCE_ORDER)
    all_available = set(list(BUILTIN_SOURCES.keys()) + custom_names)
    initial_order: list[str] = [n for n in configured_order if n in all_available]
    for n in list(BUILTIN_SOURCES.keys()) + custom_names:
        if n not in initial_order:
            initial_order.append(n)

    sources_json = json.dumps(sources_data, ensure_ascii=False).replace("</", "<\\/")
    order_json = json.dumps(initial_order, ensure_ascii=False).replace("</", "<\\/")
    builtin_info_js = json.dumps(
        {name: {"url": url} for name, url in BUILTIN_SOURCES.items()},
        ensure_ascii=False,
    ).replace("</", "<\\/")

    src_js = (
        "(function(){"
        + "var S=" + sources_json + ";"
        + "var ORDER=" + order_json + ";"
        + "var BUILTIN=" + builtin_info_js + ";"
        + r"""
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function render(){
  var c=document.getElementById('src-list');
  if(!ORDER.length){c.innerHTML='<p style="color:var(--muted);font-size:13px;padding:8px 0">No sources. Click &quot;+ Add Custom Source&quot; to add one.</p>';sync();return;}
  c.innerHTML=ORDER.map(function(name,oi){
    if(BUILTIN[name])return builtinRow(name,oi);
    var si=S.findIndex(function(s){return s.name===name;});
    return si<0?'':customRow(S[si],si,oi);
  }).join('');sync();
}
function rBtn(label,onclick,dis){
  var b='background:none;border:none;color:var(--muted);font-size:15px;line-height:1;cursor:pointer;padding:1px 5px;border-radius:3px;display:block;font-family:inherit';
  return '<button type="button" '+(dis?'disabled ':'')+' onclick="'+onclick+'" style="'+b+(dis?';opacity:0.18;cursor:default':'')+'">'+label+'</button>';
}
function rBtns(oi,n){return '<div style="display:flex;flex-direction:column;gap:0">'+rBtn('↑','oUp('+oi+')',oi===0)+rBtn('↓','oDn('+oi+')',oi>=n-1)+'</div>';}
function builtinRow(name,oi){
  var n=ORDER.length;
  return '<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:6px;margin-bottom:6px">'
    +'<span style="min-width:14px;font-size:11px;color:var(--muted);text-align:center;flex-shrink:0">'+(oi+1)+'</span>'
    +rBtns(oi,n)
    +'<div style="flex:1;min-width:0;display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
    +'<span style="font-weight:600;font-size:14px">'+esc(name)+'</span>'
    +'<span style="font-size:12px;color:var(--muted)">'+esc(BUILTIN[name].url)+'</span>'
    +'</div>'
    +'<span style="background:rgba(99,179,237,0.12);color:#63b3ed;font-size:10px;font-weight:700;padding:2px 8px;border-radius:3px;text-transform:uppercase;letter-spacing:.6px;white-space:nowrap;flex-shrink:0">Built-in</span>'
    +'</div>';
}
function sel(val,opts){return opts.map(function(o){return '<option value="'+esc(o[0])+'"'+(val===o[0]?' selected':'')+'>'+esc(o[1])+'</option>';}).join('');}
function customRow(s,si,oi){
  var n=ORDER.length;
  return '<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 14px;background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:6px;margin-bottom:6px">'
    +'<span style="min-width:14px;font-size:11px;color:var(--muted);text-align:center;flex-shrink:0;padding-top:30px">'+(oi+1)+'</span>'
    +'<div style="padding-top:26px;flex-shrink:0">'+rBtns(oi,n)+'</div>'
    +'<div style="flex:1;min-width:0">'
    +'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:4px">'
    +'<div class="field" style="flex:1;min-width:140px"><label class="field-label">Name</label>'
    +'<input value="'+esc(s.name||'')+'" oninput="sSet('+si+',\'name\',this.value)" placeholder="my-source"></div>'
    +'<div class="field"><label class="field-label">Output</label><select onchange="sSet('+si+',\'output_mode\',this.value)">'
    +sel(s.output_mode||'strm',[['strm','STRM (.strm)'],['download','Download (ffmpeg)']])
    +'</select></div>'
    +'<div class="field"><label class="field-label">Container</label><select onchange="sSet('+si+',\'container\',this.value)">'
    +sel(s.container||'mkv',[['mkv','MKV'],['mp4','MP4']])+'</select></div>'
    +'</div>'
    +'<details style="margin-top:2px"><summary style="font-size:11px;color:var(--muted);cursor:pointer;user-select:none">URL templates</summary>'
    +'<div style="display:grid;gap:6px;margin-top:6px">'
    +'<div class="field"><label class="field-label">Movie URL template</label>'
    +'<input value="'+esc(s.movie_url_template||'')+'" oninput="sSet('+si+',\'movie_url_template\',this.value)" placeholder="https://…/{tmdb_id}"></div>'
    +'<div class="field"><label class="field-label">Series URL template</label>'
    +'<input value="'+esc(s.series_url_template||'')+'" oninput="sSet('+si+',\'series_url_template\',this.value)" placeholder="https://…/{tmdb_id}/{season}/{episode}"></div>'
    +'<div class="field"><label class="field-label">Movie resolver URL</label>'
    +'<input value="'+esc(s.movie_resolver_url_template||'')+'" oninput="sSet('+si+',\'movie_resolver_url_template\',this.value)" placeholder="Returns JSON {hls_url:…}"></div>'
    +'<div class="field"><label class="field-label">Series resolver URL</label>'
    +'<input value="'+esc(s.series_resolver_url_template||'')+'" oninput="sSet('+si+',\'series_resolver_url_template\',this.value)" placeholder="Returns JSON {hls_url:…}"></div>'
    +'</div></details>'
    +'</div>'
    +'<button type="button" class="btn btn-danger btn-small" onclick="sRm('+si+')" style="align-self:center;margin-left:4px">×</button>'
    +'</div>';
}
function sync(){
  var e=document.getElementById('hls-sources-json');if(e)e.value=JSON.stringify(S);
  var o=document.getElementById('source-order-json');if(o)o.value=JSON.stringify(ORDER);
}
window.oUp=function(i){if(i===0)return;var t=ORDER[i-1];ORDER[i-1]=ORDER[i];ORDER[i]=t;render();};
window.oDn=function(i){if(i>=ORDER.length-1)return;var t=ORDER[i+1];ORDER[i+1]=ORDER[i];ORDER[i]=t;render();};
window.sSet=function(si,k,v){var old=S[si][k];S[si][k]=v;if(k==='name'){var oi=ORDER.indexOf(String(old));if(oi>=0)ORDER[oi]=v;}sync();};
window.sRm=function(si){var name=S[si].name||'?';if(!confirm('Remove "'+esc(name)+'"?'))return;S.splice(si,1);var oi=ORDER.indexOf(name);if(oi>=0)ORDER.splice(oi,1);render();};
window.srcAddNew=function(){var nm='new-source';S.push({name:nm,output_mode:'strm',container:'mkv',movie_url_template:'',series_url_template:'',movie_resolver_url_template:'',series_resolver_url_template:''});ORDER.push(nm);render();};
render();
"""
        + "})();"
    )

    return f"""
<form method="post" action="/save">
  <input type="hidden" name="_section" value="sources">
  <div class="card" id="sources">
    <div class="card-header">
      <div><div class="card-title">Sources</div>
      <div class="card-desc">Priority-ordered HLS sources — first match wins. Built-in sources (kkphim, ophim, nguonc) always available; custom sources can override or supplement.</div></div>
    </div>
    <div class="card-body">
      <div id="src-list"></div>
      <div class="actions" style="margin:10px 0 0">
        <button type="button" class="btn btn-ghost" onclick="srcAddNew()">+ Add Custom Source</button>
      </div>
      <input type="hidden" name="hls_template_sources" id="hls-sources-json" value="{_attr(templates)}">
      <input type="hidden" name="source_order_json" id="source-order-json" value="">
    </div>
  </div>
  <div class="actions">
    <button type="submit" class="btn btn-primary">&#10003; Save Sources</button>
  </div>
</form>
<script>{src_js}</script>"""
