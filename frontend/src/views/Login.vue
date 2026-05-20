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
      localStorage.setItem('deceptarr_user', username.value.trim())
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
  background:
    radial-gradient(1200px 600px at 0% 0%, rgba(94,224,189,.05), transparent 60%),
    radial-gradient(900px 600px at 100% 100%, rgba(245,166,35,.04), transparent 60%),
    var(--bg);
}
.auth-card {
  width: 100%; max-width: 360px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  padding: 32px 28px; display: flex; flex-direction: column; gap: 16px;
  box-shadow: 0 24px 60px -12px rgba(0,0,0,.6);
}
.auth-logo { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.brand-icon {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, #ffb840 0%, #f5a623 50%, #d68910 100%);
  color: #0d1218; font-weight: 700; font-size: 20px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 1px 0 rgba(255,255,255,.3) inset, 0 6px 18px -4px rgba(245,166,35,.5);
  flex-shrink: 0;
}
.brand-name { font-size: 17px; font-weight: 700; color: var(--text); }
h2 { font-size: 15px; font-weight: 600; color: var(--text); margin: 0; }
.field { display: flex; flex-direction: column; gap: 7px; }
.field label { font-size: 12px; font-weight: 600; color: var(--text-2); }
.field input {
  background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
  color: var(--text); padding: 10px 12px; font-size: 14px; outline: none;
  font-family: var(--font-sans); transition: border-color .12s;
}
.field input:focus { border-color: var(--teal); box-shadow: 0 0 0 3px rgba(94,224,189,.12); }
.btn {
  margin-top: 4px;
  background: linear-gradient(180deg, #ffb840, #f5a623);
  border: 1px solid #d68910; color: #1a1208; font-weight: 700;
  font-size: 13px; border-radius: 8px; padding: 10px; cursor: pointer;
  width: 100%; font-family: var(--font-sans);
  box-shadow: 0 1px 0 rgba(255,255,255,.3) inset, 0 4px 12px -2px rgba(245,166,35,.35);
  transition: filter .12s;
}
.btn:hover { filter: brightness(1.05); }
.btn:disabled { opacity: .5; cursor: default; filter: none; }
.err-msg { font-size: 12px; color: var(--red); background: var(--red-soft); border-radius: 7px; padding: 8px 10px; border: 1px solid rgba(255,107,107,.2); }
</style>
