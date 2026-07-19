<script setup lang="ts">
import { computed } from 'vue'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore, type ThemeMode } from '@/stores/theme'
import { formatMoney } from '@/utils/money'

const auth = useAuthStore()
const theme = useThemeStore()

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
</script>

<template>
  <div>
    <PageHeader title="Profile" subtitle="Account and appearance" />
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
          <li><span>Country</span><strong>{{ auth.user?.country || '—' }}</strong></li>
        </ul>
        <div class="actions">
          <Button as="a" href="/accounts/kyc/" label="KYC" icon="pi pi-id-card" outlined class="w-full" />
          <Button as="a" href="/accounts/setup-2fa/" label="2FA" icon="pi pi-shield" outlined class="w-full" />
          <Button label="Log out" icon="pi pi-sign-out" severity="danger" text class="w-full" @click="auth.logout()" />
        </div>
      </div>

      <div class="glass card">
        <h3>Appearance</h3>
        <p class="muted small">Theme switches instantly and is remembered on this device.</p>
        <label class="field">
          <span>Theme</span>
          <Select v-model="themeMode" :options="themes" option-label="label" option-value="value" class="w-full" />
        </label>
        <div class="preview" :data-theme-preview="theme.mode">
          <div class="mini" />
          <div class="mini short" />
        </div>
        <h3 class="mt">Classic Django UI</h3>
        <p class="muted small">Staff panel, full feature pages, and admin remain available.</p>
        <Button as="a" href="/dashboard/" label="Open classic dashboard" icon="pi pi-external-link" class="w-full" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
@media (max-width: 860px) { .grid { grid-template-columns: 1fr; } }
.card { padding: 1.25rem; }
.avatar {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #3B82F6, #7C3AED);
  margin-bottom: 0.75rem;
}
h2 { font-size: 1.25rem; }
.tags { display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.75rem 0 1rem; }
ul { list-style: none; padding: 0; margin: 0 0 1rem; display: grid; gap: 0.4rem; }
li {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.55rem 0.65rem;
  border-radius: 10px;
  background: rgba(255,255,255,0.03);
  font-size: 0.9rem;
}
li span { color: var(--ci-muted); }
.actions { display: grid; gap: 0.45rem; }
.field { display: grid; gap: 0.4rem; margin: 0.85rem 0; }
.field span { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ci-muted); font-weight: 600; }
.w-full { width: 100%; }
.preview {
  height: 88px;
  border-radius: 14px;
  border: 1px solid var(--ci-border);
  background:
    radial-gradient(circle at 80% 20%, rgba(59,130,246,0.35), transparent 45%),
    linear-gradient(145deg, rgba(255,255,255,0.06), rgba(0,0,0,0.15));
  padding: 0.85rem;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 0.4rem;
}
.mini {
  height: 12px;
  border-radius: 6px;
  background: rgba(255,255,255,0.12);
  width: 70%;
}
.mini.short { width: 40%; }
.mt { margin-top: 1.25rem; }
.small { font-size: 0.88rem; }
</style>
