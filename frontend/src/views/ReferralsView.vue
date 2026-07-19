<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import { api } from '@/services/api'
import { formatMoney, statusSeverity } from '@/utils/money'
import { useUiStore } from '@/stores/ui'
import type { ReferralData } from '@/types/api'

const router = useRouter()
const ui = useUiStore()
const loading = ref(true)
const data = ref<ReferralData | null>(null)
const leaders = ref<any[]>([])

async function load() {
  loading.value = true
  try {
    const [r, l] = await Promise.all([api.referrals(), api.leaderboard()])
    data.value = r.data
    leaders.value = l.data as any[]
  } finally {
    loading.value = false
  }
}

async function copy(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    ui.toast('Copied', 'Invite link copied', 'success')
  } catch {
    ui.toast('Copy failed', 'Copy manually', 'warn')
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Referrals" subtitle="Share your code and earn commissions" />
    <div class="grid-stats">
      <StatCard label="Referrals" :value="String(data?.stats.total_referrals ?? 0)" icon="pi pi-users" />
      <StatCard label="Earned" :value="`+${formatMoney(data?.stats.total_earned ?? 0)}`" icon="pi pi-dollar" tone="success" />
      <StatCard label="Pending" :value="formatMoney(data?.stats.pending ?? 0)" icon="pi pi-clock" tone="gold" />
      <StatCard label="Rate L1" :value="`${data?.stats.rate ?? 0}%`" icon="pi pi-percentage" />
    </div>

    <div class="glass card">
      <div class="stat-label">Your code</div>
      <div class="code mono">{{ data?.code || '—' }}</div>
      <div class="stat-label">SPA invite link</div>
      <div class="link mono">{{ data?.spa_link || '—' }}</div>
      <div class="actions">
        <Button label="Copy SPA link" icon="pi pi-copy" @click="copy(data?.spa_link || '')" />
        <Button label="Copy classic link" icon="pi pi-link" outlined @click="copy(data?.link || '')" />
      </div>
      <p class="muted small">
        Pays on {{ data?.stats.pays_on }} · L2 {{ data?.stats.rate_l2 }}% · L3 {{ data?.stats.rate_l3 }}%
      </p>
    </div>

    <div class="two">
      <div class="glass card">
        <h3>Commissions</h3>
        <DataTable :value="data?.commissions || []" :loading="loading" class="p-datatable-sm" paginator :rows="8">
          <Column field="referred_email" header="User" />
          <Column header="Amount">
            <template #body="{ data: row }"><span class="mono success">+{{ formatMoney(row.amount) }}</span></template>
          </Column>
          <Column field="level" header="Lvl" style="width:4rem" />
          <Column header="Status">
            <template #body="{ data: row }"><Tag :value="row.status" :severity="statusSeverity(row.status)" /></template>
          </Column>
          <Column header="" style="width:7rem">
            <template #body="{ data: row }">
              <Button
                label="Receipt"
                size="small"
                text
                icon="pi pi-file"
                @click="router.push(`/receipts/referral/${row.id}`)"
              />
            </template>
          </Column>
        </DataTable>
      </div>
      <div class="glass card">
        <h3>Leaderboard</h3>
        <ul class="leaders">
          <li v-for="l in leaders.slice(0, 10)" :key="l.rank" :class="{ you: l.is_you }">
            <span class="rank">#{{ l.rank }}</span>
            <span>{{ l.email }}</span>
            <span class="mono success">+{{ formatMoney(l.referral_earnings) }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}
@media (max-width: 900px) { .grid-stats { grid-template-columns: 1fr 1fr; } }
.card { padding: 1.15rem; margin-bottom: 1rem; }
.code { font-size: 1.5rem; font-weight: 800; letter-spacing: 0.06em; margin: 0.35rem 0 1rem; }
.link {
  word-break: break-all;
  padding: 0.75rem 0.85rem;
  border-radius: 12px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--ci-border);
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
}
.actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.small { font-size: 0.85rem; margin-top: 0.75rem; }
.two { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 1rem; }
@media (max-width: 960px) { .two { grid-template-columns: 1fr; } }
.leaders { list-style: none; margin: 0.75rem 0 0; padding: 0; }
.leaders li {
  display: grid;
  grid-template-columns: 2.5rem 1fr auto;
  gap: 0.5rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--ci-border);
  font-size: 0.9rem;
}
.leaders li.you { color: #60A5FA; font-weight: 700; }
.rank { color: var(--ci-muted); font-weight: 700; }
.success { color: var(--ci-success); }
</style>
