<template>
  <div class="app">
    <header class="brand">
      <div class="brand-icon">D</div>
      <span class="brand-name">Deceptarr</span>
    </header>

    <nav class="tabbar">
      <router-link to="/linkgrabber" class="tab">&#128279; LinkGrabber</router-link>
      <router-link to="/downloads" class="tab">&#11015; Downloads</router-link>
      <router-link to="/sources" class="tab">&#9733; Sources</router-link>
      <router-link to="/settings" class="tab">&#9881; Settings</router-link>
      <router-link to="/test" class="tab">&#128300; Test</router-link>
    </nav>

    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #1e2127;
  --surface: #282c34;
  --border: #3e4451;
  --text: #abb2bf;
  --text-bright: #d7dae0;
  --muted: #5c6370;
  --accent: #61afef;
  --green: #98c379;
  --red: #e06c75;
  --input-bg: #1a1d23;
}

body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; font-size: 14px; }

.app { display: flex; flex-direction: column; height: 100vh; }

.brand {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 18px; background: var(--surface); border-bottom: 1px solid var(--border);
}
.brand-icon {
  width: 28px; height: 28px; border-radius: 6px; background: var(--accent);
  color: #1e2127; font-weight: 700; font-size: 15px;
  display: flex; align-items: center; justify-content: center;
}
.brand-name { font-size: 16px; font-weight: 600; color: var(--text-bright); }

.tabbar {
  display: flex; background: var(--surface); border-bottom: 2px solid var(--border);
  padding: 0 8px;
}
.tab {
  padding: 10px 18px; cursor: pointer; font-size: 13px; color: var(--muted);
  text-decoration: none; border-bottom: 2px solid transparent; margin-bottom: -2px;
  transition: color .15s, border-color .15s;
}
.tab:hover { color: var(--text-bright); }
.tab.router-link-active { color: var(--accent); border-bottom-color: var(--accent); }

.content { flex: 1; overflow-y: auto; padding: 24px 28px; max-width: 980px; width: 100%; margin: 0 auto; }
</style>
