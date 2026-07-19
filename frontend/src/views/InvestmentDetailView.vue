<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import ProgressBar from 'primevue/progressbar'
import Tag from 'primevue/tag'
import Skeleton from 'primevue/skeleton'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { formatMoney, shortDate, statusSeverity } from '@/utils/money'
import type { Investment } from '@/types/api'

const route = useRoute()
const router = useRouter()
const inv = ref<Investment | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.investment(String(route.params.id))
    inv.value = data
  } catch {
    router.push('/investments')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader :title="inv?.plan_name || 'Investment'" subtitle="Position details">
      <Button label="Back" icon="pi pi-arrow-left" text @click="router.push('/investments')" />
      <Button
        v-if="inv"
        label="Receipt"
        icon="pi pi-file"
        outlined
        @click="router.push(`/receipts/investment/${inv.id}`)"
      />
    </PageHeader>
    <Skeleton v-if="loading" height="220px" border-radius="18px" />
    <div v-else-if="inv" class="glass card">
      <div class="top">
        <Tag :value="inv.status" :severity="statusSeverity(inv.status)" />
        <span class="muted">{{ inv.payout_frequency }} · {{ inv.duration_days }} days</span>
      </div>
      <div class="grid">
        <div><div class="stat-label">Amount</div><div class="mono val">{{ formatMoney(inv.amount) }}</div></div>
        <div><div class="stat-label">Earned</div><div class="mono val success">+{{ formatMoney(inv.total_earned) }}</div></div>
        <div><div class="stat-label">Rate</div><div class="mono val">{{ inv.profit_rate_percent }}%</div></div>
        <div><div class="stat-label">Payouts</div><div class="mono val">{{ inv.payouts_count }}/{{ inv.expected_payouts }}</div></div>
      </div>
      <div class="stat-label">Progress</div>
      <ProgressBar :value="inv.progress_percent || 0" />
      <div class="meta muted small">
        <span>Started {{ shortDate(inv.started_at) }}</span>
        <span>Matures {{ shortDate(inv.matures_at) }}</span>
        <span v-if="inv.next_payout_at">Next payout {{ shortDate(inv.next_payout_at) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 1.25rem; max-width: 720px; }
.top { display: flex; justify-content: space-between; margin-bottom: 1rem; }
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}
@media (max-width: 700px) { .grid { grid-template-columns: 1fr 1fr; } }
.val { font-size: 1.15rem; font-weight: 750; margin-top: 0.2rem; }
.success { color: var(--ci-success); }
.meta { display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 0.85rem; }
.small { font-size: 0.85rem; }
</style>
