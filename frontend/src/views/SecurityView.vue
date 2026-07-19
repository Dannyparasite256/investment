<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import Password from 'primevue/password'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const auth = useAuthStore()
const ui = useUiStore()
const current = ref('')
const next = ref('')
const confirm = ref('')
const saving = ref(false)

async function changePassword() {
  if (next.value.length < 8) {
    ui.toast('Too short', 'Password must be at least 8 characters', 'warn')
    return
  }
  if (next.value !== confirm.value) {
    ui.toast('Mismatch', 'New passwords do not match', 'warn')
    return
  }
  saving.value = true
  try {
    const { data } = await api.changePassword(current.value, next.value)
    if (data.token) {
      auth.token = data.token
      localStorage.setItem('ci_token', data.token)
    }
    current.value = ''
    next.value = ''
    confirm.value = ''
    ui.toast('Updated', 'Password changed successfully', 'success')
  } catch (e: any) {
    const msg = e?.response?.data?.current_password?.[0]
      || e?.response?.data?.detail
      || 'Could not change password'
    ui.toast('Failed', msg, 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader title="Security" subtitle="Password and two-factor authentication" />
    <div class="grid">
      <div class="glass card">
        <h3>Change password</h3>
        <div class="form">
          <label>Current password
            <Password v-model="current" :feedback="false" toggle-mask class="w-full" input-class="w-full" />
          </label>
          <label>New password
            <Password v-model="next" toggle-mask class="w-full" input-class="w-full" />
          </label>
          <label>Confirm new password
            <Password v-model="confirm" :feedback="false" toggle-mask class="w-full" input-class="w-full" />
          </label>
          <Button label="Update password" icon="pi pi-lock" :loading="saving" @click="changePassword" />
        </div>
      </div>
      <div class="glass card">
        <h3>Two-factor authentication</h3>
        <p class="muted">
          Status:
          <Tag
            :value="auth.user?.two_factor_enabled ? 'Enabled' : 'Disabled'"
            :severity="auth.user?.two_factor_enabled ? 'success' : 'secondary'"
          />
        </p>
        <p class="muted small">
          Set up authenticator-app 2FA in the classic secure flow (QR + recovery codes).
        </p>
        <Button as="a" href="/accounts/2fa/setup/" label="Open 2FA setup" icon="pi pi-shield" class="w-full" />
        <Button as="a" href="/accounts/password-reset/" label="Forgot password?" text class="w-full mt" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
.card { padding: 1.15rem; }
.form { display: flex; flex-direction: column; gap: 0.75rem; margin-top: 0.75rem; }
.form label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.85rem; font-weight: 600; color: var(--ci-muted); }
.small { font-size: 0.85rem; }
.mt { margin-top: 0.5rem; }
:deep(.p-password) { width: 100%; }
</style>
