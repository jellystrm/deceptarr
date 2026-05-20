<template>
  <div class="auth-wrap">
    <div class="auth-card">
      <div class="auth-logo">
        <div class="brand-icon">D</div>
        <span class="brand-name">Deceptarr</span>
      </div>
      <h2>Create your account</h2>
      <p class="sub">Set up the admin account to secure this instance.</p>

      <div class="field">
        <label>Username</label>
        <input v-model="username" type="text" placeholder="admin" autocomplete="username" @keydown.enter="submit" />
      </div>
      <div class="field">
        <label>Password</label>
        <input v-model="password" type="password" placeholder="••••••••" autocomplete="new-password" @keydown.enter="submit" />
      </div>
      <div class="field">
        <label>Confirm password</label>
        <input v-model="confirm" type="password" placeholder="••••••••" autocomplete="new-password" @keydown.enter="submit" />
      </div>

      <div v-if="error" class="err-msg">{{ error }}</div>

      <button class="btn" :disabled="loading" @click="submit">
        {{ loading ? 'Creating…' : 'Create account' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authSetup } from '../api'

const router = useRouter()
const username = ref('')
const password = ref('')
const confirm  = ref('')
const error    = ref('')
const loading  = ref(false)

async function submit() {
  error.value = ''
  if (!username.value.trim()) { error.value = 'Username is required'; return }
  if (password.value.length < 4) { error.value = 'Password must be at least 4 characters'; return }
  if (password.value !== confirm.value) { error.value = 'Passwords do not match'; return }
  loading.value = true
  try {
    const res = await authSetup(username.value.trim(), password.value)
    if (res.status === 'ok') {
      router.replace('/downloads')
    } else {
      error.value = res.error || 'Setup failed'
    }
  } catch (e: unknown) {
    error.value = String(e)
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
  width: 100%; max-width: 380px;
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
.sub { font-size: 12px; color: var(--muted); margin-top: -8px; }
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
