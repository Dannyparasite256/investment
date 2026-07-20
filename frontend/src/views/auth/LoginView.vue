<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const auth = useAuthStore()
const theme = useThemeStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const otpCode = ref('')
const info = ref('')

const needsOtp = computed(() => !!auth.otpChallenge)

async function submitPassword() {
  info.value = ''
  auth.clearOtpState()
  const result = await auth.login(email.value.trim(), password.value)
  if (result.ok) {
    const next = (route.query.next as string) || '/dashboard'
    router.replace(next)
    return
  }
  if (result.needsOtp && auth.otpChallenge) {
    info.value = auth.otpChallenge.detail
    otpCode.value = ''
  }
}

async function submitOtp() {
  info.value = ''
  const method = auth.otpChallenge?.method || 'email'
  const ok = await auth.verifyOtp(otpCode.value.trim(), method)
  if (ok) {
    const next = (route.query.next as string) || '/dashboard'
    router.replace(next)
  }
}

async function resend() {
  info.value = ''
  await auth.resendEmailOtp()
  if (auth.otpChallenge?.detail) {
    info.value = auth.otpChallenge.detail
  }
}

async function useEmailInstead() {
  info.value = ''
  await auth.requestEmailOtpFallback()
  if (auth.otpChallenge?.detail) {
    info.value = auth.otpChallenge.detail
  }
}

function backToPassword() {
  auth.clearOtpState()
  otpCode.value = ''
  info.value = ''
  auth.error = ''
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
        <h1 class="gradient-text">CryptoInvest</h1>
        <p class="muted">
          {{ needsOtp
            ? (auth.otpChallenge?.method === 'totp'
              ? 'Enter your authenticator code'
              : 'Enter the code we emailed you')
            : 'Welcome back to your portfolio' }}
        </p>
      </div>

      <Message v-if="auth.error" severity="error" :closable="false" class="mb">{{ auth.error }}</Message>
      <Message v-else-if="info" severity="info" :closable="false" class="mb">{{ info }}</Message>

      <form v-if="!needsOtp" class="form" @submit.prevent="submitPassword">
        <label class="field">
          <span>Email</span>
          <InputText v-model="email" type="email" autocomplete="username" required fluid placeholder="you@email.com" />
        </label>
        <label class="field">
          <span>Password</span>
          <Password v-model="password" :feedback="false" toggle-mask input-class="w-full" class="w-full" fluid required />
        </label>
        <Button type="submit" label="Log in" icon="pi pi-sign-in" class="w-full" :loading="auth.loading" />
      </form>

      <form v-else class="form" @submit.prevent="submitOtp">
        <label class="field">
          <span>{{ auth.otpChallenge?.method === 'totp' ? 'Authenticator code' : 'Email code' }}</span>
          <InputText
            v-model="otpCode"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="6"
            required
            fluid
            placeholder="000000"
            class="otp-input"
          />
        </label>
        <Button type="submit" label="Verify & continue" icon="pi pi-check" class="w-full" :loading="auth.loading" />
        <Button
          v-if="auth.otpChallenge?.method === 'email' || auth.otpChallenge?.emailFallback"
          type="button"
          label="Resend email code"
          severity="secondary"
          text
          class="w-full"
          :loading="auth.loading"
          @click="resend"
        />
        <Button
          v-if="auth.otpChallenge?.method === 'totp' && auth.otpChallenge?.emailFallback"
          type="button"
          label="Send code to my email instead"
          severity="secondary"
          text
          class="w-full"
          :loading="auth.loading"
          @click="useEmailInstead"
        />
        <Button type="button" label="Back" severity="secondary" text class="w-full" @click="backToPassword" />
      </form>

      <p class="foot muted">
        No account?
        <RouterLink to="/register">Create one</RouterLink>
        ·
        <a href="/accounts/password-reset/">Forgot password</a>
      </p>
      <p class="foot muted small">
        Prefer classic site?
        <a href="/accounts/login/">Open Django login</a>
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
  padding-top: calc(1.5rem + env(safe-area-inset-top, 0px));
  padding-bottom: calc(1.5rem + env(safe-area-inset-bottom, 0px));
  position: relative;
}
@media (max-width: 480px) {
  .auth { padding: 1rem; align-items: flex-start; padding-top: 3.5rem; }
  .card {
    width: 100%;
    max-width: 100%;
    padding: 1.25rem 1rem;
  }
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
.logo {
  text-align: center;
  margin-bottom: 1.5rem;
}
.mark {
  width: 52px;
  height: 52px;
  margin: 0 auto 0.65rem;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #3B82F6, #7C3AED);
  box-shadow: 0 10px 28px rgba(59, 130, 246, 0.45);
}
h1 {
  font-size: 1.45rem;
  font-weight: 800;
}
.logo p {
  margin: 0.35rem 0 0;
  font-size: 0.9rem;
}
.form {
  display: grid;
  gap: 0.9rem;
}
.field {
  display: grid;
  gap: 0.35rem;
}
.field span {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--ci-muted);
}
.w-full { width: 100%; }
.mb { margin-bottom: 0.85rem; }
.foot {
  text-align: center;
  margin: 1.15rem 0 0;
  font-size: 0.88rem;
}
.foot a {
  color: #60A5FA;
  font-weight: 600;
}
.small { font-size: 0.8rem; opacity: 0.85; }
.otp-input :deep(input),
:deep(.otp-input) {
  text-align: center;
  letter-spacing: 0.35em;
  font-size: 1.25rem;
  font-weight: 700;
}
:deep(.p-password) { width: 100%; }
:deep(.p-password-input) { width: 100%; }
</style>
