<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { api } from '@/services/api'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
const router = useRouter()

const step = ref<'email' | 'code'>('email')
const email = ref('')
const code = ref('')
const password = ref('')
const password2 = ref('')
const loading = ref(false)
const error = ref('')
const info = ref('')

async function sendCode() {
  loading.value = true
  error.value = ''
  info.value = ''
  try {
    const { data } = await api.requestPasswordReset(email.value.trim())
    info.value = data.detail || 'Check your email for a 6-digit code.'
    step.value = 'code'
  } catch (e: any) {
    error.value = e?.response?.data?.email?.[0]
      || e?.response?.data?.detail
      || 'Could not send reset email. Try again.'
  } finally {
    loading.value = false
  }
}

async function resetPassword() {
  error.value = ''
  if (password.value !== password2.value) {
    error.value = 'Passwords do not match.'
    return
  }
  if (password.value.length < 8) {
    error.value = 'Password must be at least 8 characters.'
    return
  }
  loading.value = true
  try {
    const { data } = await api.confirmPasswordReset({
      email: email.value.trim(),
      code: code.value.trim(),
      new_password: password.value,
    })
    info.value = data.detail || 'Password updated.'
    setTimeout(() => router.replace('/login'), 1200)
  } catch (e: any) {
    const d = e?.response?.data
    error.value = d?.detail
      || d?.new_password?.[0]
      || 'Could not reset password. Check the code and try again.'
  } finally {
    loading.value = false
  }
}

async function resend() {
  await sendCode()
}
</script>

<template>
  <div class="auth">
    <button type="button" class="theme-btn" @click="theme.toggleDarkLight()" aria-label="Theme">
      <i :class="theme.mode === 'light' ? 'pi pi-sun' : 'pi pi-moon'" />
    </button>
    <div class="card glass">
      <div class="logo">
        <div class="mark">C</div>
        <h1 class="gradient-text">Reset password</h1>
        <p class="muted">
          {{ step === 'email' ? 'We will email you a free 6-digit code' : 'Enter the code and your new password' }}
        </p>
      </div>

      <Message v-if="error" severity="error" :closable="false" class="mb">{{ error }}</Message>
      <Message v-else-if="info" severity="info" :closable="false" class="mb">{{ info }}</Message>

      <form v-if="step === 'email'" class="form" @submit.prevent="sendCode">
        <label class="field">
          <span>Account email</span>
          <InputText v-model="email" type="email" required fluid placeholder="you@email.com" autocomplete="email" />
        </label>
        <Button type="submit" label="Send reset code" icon="pi pi-envelope" class="w-full" :loading="loading" />
      </form>

      <form v-else class="form" @submit.prevent="resetPassword">
        <label class="field">
          <span>Email code</span>
          <InputText
            v-model="code"
            inputmode="numeric"
            maxlength="6"
            required
            fluid
            placeholder="000000"
            autocomplete="one-time-code"
            class="otp-input"
          />
        </label>
        <label class="field">
          <span>New password</span>
          <Password v-model="password" :feedback="false" toggle-mask class="w-full" input-class="w-full" fluid required />
        </label>
        <label class="field">
          <span>Confirm password</span>
          <Password v-model="password2" :feedback="false" toggle-mask class="w-full" input-class="w-full" fluid required />
        </label>
        <Button type="submit" label="Update password" icon="pi pi-check" class="w-full" :loading="loading" />
        <Button type="button" label="Resend code" text severity="secondary" class="w-full" :loading="loading" @click="resend" />
        <Button type="button" label="Use a different email" text severity="secondary" class="w-full" @click="step = 'email'" />
      </form>

      <p class="foot muted">
        <RouterLink to="/login">Back to login</RouterLink>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth {
  min-height: 100dvh;
  min-height: 100svh;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  position: relative;
}
.theme-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  border: 1px solid var(--ci-border);
  background: var(--ci-surface);
  color: var(--ci-text);
  width: 40px;
  height: 40px;
  border-radius: 12px;
  cursor: pointer;
}
.card {
  width: min(420px, 100%);
  padding: 2rem 1.75rem;
}
.logo { text-align: center; margin-bottom: 1.5rem; }
.mark {
  width: 52px; height: 52px; margin: 0 auto 0.65rem; border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; color: #fff;
  background: linear-gradient(135deg, #3B82F6, #7C3AED);
}
h1 { font-size: 1.35rem; font-weight: 800; }
.logo p { margin: 0.35rem 0 0; font-size: 0.9rem; }
.form { display: grid; gap: 0.9rem; }
.field { display: grid; gap: 0.35rem; }
.field span {
  font-size: 0.78rem; font-weight: 600; letter-spacing: 0.03em;
  text-transform: uppercase; color: var(--ci-muted);
}
.w-full { width: 100%; }
.mb { margin-bottom: 0.85rem; }
.foot { text-align: center; margin: 1.15rem 0 0; font-size: 0.88rem; }
.foot a { color: #60A5FA; font-weight: 600; }
.otp-input :deep(input), :deep(.otp-input) {
  text-align: center; letter-spacing: 0.35em; font-size: 1.25rem; font-weight: 700;
}
:deep(.p-password) { width: 100%; }
:deep(.p-password-input) { width: 100%; }
</style>
