<template>
  <div class="auth-wrap">
    <div class="auth-card">
      <div class="auth-logo">
        <div class="brand-icon">D</div>
        <span class="brand-name">Deceptarr</span>
      </div>
      <h2>Sign in</h2>

      <div class="field">
        <label>Username</label>
        <input v-model="username" type="text" placeholder="admin" autocomplete="username" @keydown.enter="submit" />
      </div>
      <div class="field">
        <label>Password</label>
        <input v-model="password" type="password" placeholder="••••••••" autocomplete="current-password" @keydown.enter="submit" />
      </div>

      <div v-if="error" class="err-msg">{{ error }}</div>

      <button class="btn" :disabled="loading" @click="submit">
        {{ loading ? 'Signing in…' : 'Sign in' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authLogin } from '../api'

const router = useRouter()
const route  = useRoute()
const username = ref('')
const password = ref('')
const error    = ref('')
const loading  = ref(false)

async function submit() {
  error.value = ''
  if (!username.value.trim() || !password.value) { error.value = 'Enter username and password'; return }
  loading.value = true
  try {
    const res = await authLogin(username.value.trim(), password.value)
    if (res.status === 'ok') {
      const next = (route.query.next as string) || '/downloads'
      router.replace(next)
    } else {
      error.value = res.error || 'Login failed'
    }
  } catch (e: unknown) {
    error.value = 'Invalid username or password'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: var(--bg);
}
.auth-card {
  width: 100%; max-width: 360px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 32px 28px; display: flex; flex-direction: column; gap: 14px;
}
.auth-logo { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.brand-icon {
  width: 30px; height: 30px; border-radius: 7px; background: var(--accent);
  color: #1e2127; font-weight: 700; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
}
.brand-name { font-size: 17px; font-weight: 700; color: var(--text-bright); }
h2 { font-size: 15px; font-weight: 600; color: var(--text-bright); margin: 0; }
.field { display: flex; flex-direction: column; gap: 5px; }
.field label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
.field input {
  background: var(--input-bg); border: 1px solid var(--border); border-radius: 6px;
  color: var(--text-bright); padding: 8px 11px; font-size: 13px; outline: none;
}
.field input:focus { border-color: var(--accent); }
.btn {
  margin-top: 4px; background: var(--accent); color: #1e2127; font-weight: 700;
  font-size: 13px; border: none; border-radius: 6px; padding: 9px; cursor: pointer;
  width: 100%;
}
.btn:disabled { opacity: .5; cursor: default; }
.err-msg { font-size: 12px; color: var(--red); background: rgba(224,108,117,.1); border-radius: 5px; padding: 8px 10px; }
</style>
