<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Select from 'primevue/select'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'
import PageHeader from '@/components/ui/PageHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore, type ThemeMode } from '@/stores/theme'
import { api } from '@/services/api'
import { formatMoney } from '@/utils/money'
import { useUiStore } from '@/stores/ui'

const auth = useAuthStore()
const theme = useThemeStore()
const ui = useUiStore()
const router = useRouter()
const saving = ref(false)
const pushBusy = ref(false)
const pushSupported = ref(false)
const pushPermission = ref<NotificationPermission | 'unsupported'>('default')
const pushEnabled = ref(false)
const vapidKey = ref('')
const pushReady = ref(false)

const form = ref({
  first_name: '',
  last_name: '',
  phone: '',
  country: '',
  preferred_currency: '',
  email_alerts: true,
  sms_alerts: false,
})

const themes = [
  { label: 'Dark (Premium)', value: 'dark' },
  { label: 'Light', value: 'light' },
  { label: 'Glass', value: 'glass' },
  { label: 'Classic', value: 'classic' },
]

const themeMode = computed({
  get: () => theme.mode,
  set: (v: ThemeMode) => theme.apply(v),
})

const pushStatusLabel = computed(() => {
  if (!pushSupported.value) return 'Not supported in this browser'
  if (!vapidKey.value) return 'Server push keys not configured yet'
  if (pushPermission.value === 'denied') return 'Blocked in browser settings'
  if (pushEnabled.value) return 'Enabled on this device'
  return 'Optional browser notifications for deposits, support, and alerts'
})

function urlBase64ToUint8Array(base64String: string) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(base64)
  const out = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i)
  return out
}

async function loadPushState() {
  pushSupported.value =
    typeof window !== 'undefined' &&
    'Notification' in window &&
    'serviceWorker' in navigator &&
    'PushManager' in window
  if (!pushSupported.value) {
    pushPermission.value = 'unsupported'
    return
  }
  pushPermission.value = Notification.permission
  try {
    let boot: any = null
    try {
      boot = JSON.parse(localStorage.getItem('ci_bootstrap') || 'null')
    } catch { /* */ }
    if (!boot?.vapid_public_key) {
      const { data } = await api.bootstrap()
      boot = data
      try { localStorage.setItem('ci_bootstrap', JSON.stringify(data)) } catch { /* */ }
    }
    vapidKey.value = (boot?.vapid_public_key || '').trim()
    pushReady.value = Boolean(boot?.push_enabled !== false && vapidKey.value)

    if (Notification.permission === 'granted' && navigator.serviceWorker) {
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.getSubscription()
      pushEnabled.value = !!sub
    }
  } catch {
    pushReady.value = false
  }
}

async function enablePush() {
  if (!pushSupported.value) {
    ui.toast('Unavailable', 'This browser does not support Web Push', 'warn')
    return
  }
  if (!vapidKey.value) {
    ui.toast(
      'Not configured',
      'Ask an admin to set VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY on the server',
      'warn',
    )
    return
  }
  pushBusy.value = true
  try {
    const perm = await Notification.requestPermission()
    pushPermission.value = perm
    if (perm !== 'granted') {
      ui.toast('Permission denied', 'Enable notifications in browser settings to continue', 'warn')
      return
    }
    const reg = await navigator.serviceWorker.ready
    let sub = await reg.pushManager.getSubscription()
    if (!sub) {
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey.value),
      })
    }
    const json = sub.toJSON()
    await api.pushSubscribe({
      endpoint: sub.endpoint,
      keys: {
        p256dh: json.keys?.p256dh,
        auth: json.keys?.auth,
      },
    })
    pushEnabled.value = true
    ui.toast('Push enabled', 'You will get browser alerts on this device', 'success')
  } catch (e: any) {
    ui.toast('Push failed', e?.response?.data?.detail || e?.message || 'Could not subscribe', 'error')
  } finally {
    pushBusy.value = false
  }
}

async function disablePush() {
  pushBusy.value = true
  try {
    const reg = await navigator.serviceWorker.ready
    const sub = await reg.pushManager.getSubscription()
    if (sub) {
      try {
        await api.pushUnsubscribe(sub.endpoint)
      } catch { /* best effort */ }
      await sub.unsubscribe()
    }
    pushEnabled.value = false
    ui.toast('Push disabled', 'Browser alerts turned off on this device', 'info')
  } catch (e: any) {
    ui.toast('Failed', e?.message || 'Could not unsubscribe', 'error')
  } finally {
    pushBusy.value = false
  }
}

onMounted(() => {
  const u = auth.user
  if (u) {
    form.value = {
      first_name: u.first_name || '',
      last_name: u.last_name || '',
      phone: u.phone || '',
      country: u.country || '',
      preferred_currency: u.preferred_currency || '',
      email_alerts: u.email_alerts !== false,
      sms_alerts: !!u.sms_alerts,
    }
  }
  loadPushState()
})

async function save() {
  saving.value = true
  try {
    await api.updateProfile(form.value)
    await auth.fetchMe()
    ui.toast('Saved', 'Profile updated', 'success')
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Could not save', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader title="Profile" subtitle="Account, preferences, and security" />
    <div class="grid">
      <div class="glass card">
        <div class="avatar">
          <img
            v-if="auth.user?.avatar_url"
            :src="auth.user.avatar_url"
            :alt="auth.displayName"
            class="avatar-img"
            referrerpolicy="no-referrer"
          />
          <template v-else>{{ (auth.displayName || 'U').slice(0, 1).toUpperCase() }}</template>
        </div>
        <h2>{{ auth.displayName }}</h2>
        <p class="muted">{{ auth.user?.email }}</p>
        <div class="tags">
          <Tag v-if="auth.user?.email_verified" value="Email verified" severity="success" />
          <Tag v-else value="Email pending" severity="warn" />
          <Tag v-if="auth.user?.is_kyc_verified" value="KYC verified" severity="success" />
          <Tag v-else value="KYC incomplete" severity="info" />
          <Tag v-if="auth.user?.two_factor_enabled" value="2FA on" severity="info" />
        </div>
        <ul>
          <li><span>Referral code</span><strong class="mono">{{ auth.user?.referral_code || '—' }}</strong></li>
          <li><span>Referral earnings</span><strong class="mono success">+{{ formatMoney(auth.user?.referral_earnings ?? 0) }}</strong></li>
          <li><span>Risk score</span><strong>{{ auth.user?.risk_score ?? 0 }}</strong></li>
        </ul>
        <div class="actions">
          <Button label="KYC" icon="pi pi-id-card" outlined class="w-full" @click="router.push('/kyc')" />
          <Button label="Security" icon="pi pi-shield" outlined class="w-full" @click="router.push('/security')" />
          <Button label="VIP" icon="pi pi-crown" outlined class="w-full" @click="router.push('/vip')" />
          <Button label="Log out" icon="pi pi-sign-out" severity="danger" text class="w-full" @click="auth.logout()" />
        </div>
      </div>

      <div class="stack">
        <div class="glass card">
          <h3>Edit profile</h3>
          <div class="form">
            <label>First name <InputText v-model="form.first_name" class="w-full" /></label>
            <label>Last name <InputText v-model="form.last_name" class="w-full" /></label>
            <label>Phone <InputText v-model="form.phone" class="w-full" /></label>
            <label>Country <InputText v-model="form.country" class="w-full" /></label>
            <label>Display currency <InputText v-model="form.preferred_currency" class="w-full" placeholder="e.g. USDT" /></label>
            <div class="switch-row">
              <span>Email alerts</span>
              <ToggleSwitch v-model="form.email_alerts" />
            </div>
            <div class="switch-row">
              <span>SMS alerts</span>
              <ToggleSwitch v-model="form.sms_alerts" />
            </div>
            <Button label="Save profile" icon="pi pi-check" :loading="saving" @click="save" />
          </div>
        </div>

        <div class="glass card">
          <h3>Appearance</h3>
          <label class="field">
            <span>Theme</span>
            <Select v-model="themeMode" :options="themes" option-label="label" option-value="value" class="w-full" />
          </label>
          <div class="preview" :data-theme-preview="theme.mode">
            <div class="mini" />
            <div class="mini short" />
          </div>
        </div>

        <div class="glass card push-card">
          <h3>Browser push</h3>
          <p class="muted push-desc">{{ pushStatusLabel }}</p>
          <div class="push-row">
            <Tag
              v-if="pushEnabled"
              value="On"
              severity="success"
            />
            <Tag
              v-else-if="pushPermission === 'denied'"
              value="Blocked"
              severity="danger"
            />
            <Tag
              v-else-if="!vapidKey"
              value="Setup needed"
              severity="warn"
            />
            <Tag
              v-else
              value="Off"
              severity="secondary"
            />
            <Button
              v-if="!pushEnabled"
              label="Enable push alerts"
              icon="pi pi-bell"
              :loading="pushBusy"
              :disabled="!pushSupported || pushPermission === 'denied'"
              @click="enablePush"
            />
            <Button
              v-else
              label="Disable on this device"
              icon="pi pi-bell-slash"
              severity="secondary"
              outlined
              :loading="pushBusy"
              @click="disablePush"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1.2fr; gap: 1rem; }
@media (max-width: 900px) {
  .grid { grid-template-columns: 1fr; gap: 0.75rem; }
}
.stack { display: flex; flex-direction: column; gap: 1rem; }
.card { padding: 1.25rem; }
@media (max-width: 640px) {
  .card { padding: 1rem 0.85rem; }
  .avatar { width: 56px; height: 56px; font-size: 1.2rem; }
  h2 { font-size: 1.15rem; word-break: break-word; }
  li {
    flex-wrap: wrap;
    font-size: 0.85rem;
  }
  .push-row {
    flex-direction: column;
    align-items: stretch;
  }
  .push-row :deep(.p-button) { width: 100%; justify-content: center; }
}
.avatar {
  width: 64px; height: 64px; border-radius: 18px;
  display: grid; place-items: center; font-weight: 800; font-size: 1.4rem;
  background: linear-gradient(135deg, #3B82F6, #7C3AED); color: #fff; margin-bottom: 0.75rem;
  overflow: hidden;
}
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.tags { display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.75rem 0; }
ul { list-style: none; padding: 0; margin: 0 0 1rem; }
li { display: flex; justify-content: space-between; gap: 0.5rem; padding: 0.45rem 0; border-bottom: 1px solid var(--ci-border); font-size: 0.9rem; }
.actions { display: grid; gap: 0.45rem; }
.form { display: grid; gap: 0.65rem; margin-top: 0.75rem; }
.form label, .field { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.85rem; font-weight: 600; color: var(--ci-muted); }
.switch-row { display: flex; justify-content: space-between; align-items: center; font-weight: 600; font-size: 0.9rem; }
.w-full { width: 100%; }
.success { color: var(--ci-success); }
.preview {
  margin-top: 0.85rem; padding: 1rem; border-radius: 14px;
  background: rgba(255,255,255,0.04); border: 1px solid var(--ci-border);
  display: flex; flex-direction: column; gap: 0.45rem;
}
.mini { height: 10px; border-radius: 99px; background: linear-gradient(90deg, #3B82F6, #7C3AED); width: 70%; }
.mini.short { width: 40%; opacity: 0.5; }
.push-card h3 { margin-bottom: 0.35rem; }
.push-desc { font-size: 0.88rem; margin: 0 0 0.85rem; }
.push-row { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; }
</style>
