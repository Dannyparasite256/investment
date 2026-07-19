<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import PageHeader from '@/components/ui/PageHeader.vue'
import Button from 'primevue/button'
import { formatMoney } from '@/utils/money'
import { useUiStore } from '@/stores/ui'
import { computed } from 'vue'

const auth = useAuthStore()
const ui = useUiStore()
const link = computed(() => {
  const code = auth.user?.referral_code || ''
  return `${window.location.origin}/accounts/register/?ref=${code}`
})

async function copy() {
  try {
    await navigator.clipboard.writeText(link.value)
    ui.toast('Copied', 'Invite link copied to clipboard', 'success')
  } catch {
    ui.toast('Copy failed', 'Select and copy the link manually', 'warn')
  }
}
</script>

<template>
  <div>
    <PageHeader title="Referrals" subtitle="Share your code and earn commissions" />
    <div class="glass card">
      <div class="stat-label">Your code</div>
      <div class="code mono">{{ auth.user?.referral_code || '—' }}</div>
      <div class="stat-label mt">Invite link</div>
      <div class="link mono">{{ link }}</div>
      <Button label="Copy invite link" icon="pi pi-copy" class="mt" @click="copy" />
      <p class="muted mt">
        Referral earnings:
        <strong class="success mono">+{{ formatMoney(auth.user?.referral_earnings ?? 0) }}</strong>
      </p>
      <p class="muted small">
        Advanced affiliate stats remain available in the classic Django UI.
        <a href="/referrals/">Open classic referrals →</a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 1.25rem; max-width: 640px; }
.code {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  margin: 0.35rem 0 1rem;
}
.link {
  word-break: break-all;
  padding: 0.75rem 0.85rem;
  border-radius: 12px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--ci-border);
  font-size: 0.88rem;
}
.mt { margin-top: 0.85rem; }
.small { font-size: 0.85rem; }
.small a { color: #60A5FA; font-weight: 600; }
</style>
