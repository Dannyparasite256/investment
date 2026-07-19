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

onMounted(() => {
  const u = auth.user
  if (!u) return
  form.value = {
    first_name: u.first_name || '',
    last_name: u.last_name || '',
    phone: u.phone || '',
    country: u.country || '',
    preferred_currency: u.preferred_currency || '',
    email_alerts: u.email_alerts !== false,
    sms_alerts: !!u.sms_alerts,
  }
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
        <div class="avatar">{{ (auth.displayName || 'U').slice(0, 1).toUpperCase() }}</div>
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
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1.2fr; gap: 1rem; }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
.stack { display: flex; flex-direction: column; gap: 1rem; }
.card { padding: 1.25rem; }
.avatar {
  width: 64px; height: 64px; border-radius: 18px;
  display: grid; place-items: center; font-weight: 800; font-size: 1.4rem;
  background: linear-gradient(135deg, #3B82F6, #7C3AED); color: #fff; margin-bottom: 0.75rem;
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
</style>
