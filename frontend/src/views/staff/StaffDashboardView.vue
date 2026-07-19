<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Skeleton from 'primevue/skeleton'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import { api } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'

const router = useRouter()
const loading = ref(true)
const data = ref<any>(null)

onMounted(async () => {
  try {
    const res = await api.staffDashboard()
    data.value = res.data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="Admin dashboard" subtitle="Staff operations panel">
      <Button label="Deposits queue" icon="pi pi-download" @click="router.push('/admin/deposits')" />
      <Button label="Withdrawals" icon="pi pi-upload" outlined @click="router.push('/admin/withdrawals')" />
      <Button as="a" href="/staff/" label="Classic staff" icon="pi pi-external-link" text />
    </PageHeader>

    <div v-if="loading" class="grid-stats">
      <Skeleton v-for="i in 6" :key="i" height="96px" border-radius="16px" />
    </div>
    <div v-else class="grid-stats">
      <StatCard label="Users" :value="String(data?.stats?.users_total ?? 0)" icon="pi pi-users" />
      <StatCard label="Pending deposits" :value="String(data?.stats?.deposits_pending ?? 0)" icon="pi pi-download" tone="gold" />
      <StatCard label="Pending withdraw" :value="String(data?.stats?.withdrawals_pending ?? 0)" icon="pi pi-upload" />
      <StatCard label="KYC queue" :value="String(data?.stats?.kyc_pending ?? 0)" icon="pi pi-id-card" />
      <StatCard label="Active investments" :value="String(data?.stats?.active_investments ?? 0)" icon="pi pi-briefcase" />
      <StatCard label="Open tickets" :value="String(data?.stats?.open_tickets ?? 0)" icon="pi pi-comments" />
    </div>

    <div class="sums glass">
      <div><span class="muted">Deposits pending</span><strong class="mono">{{ data?.stats?.deposits_pending_sum }}</strong></div>
      <div><span class="muted">Withdrawals pending</span><strong class="mono">{{ data?.stats?.withdrawals_pending_sum }}</strong></div>
      <div><span class="muted">Invested total</span><strong class="mono">{{ data?.stats?.invested_total }}</strong></div>
      <div><span class="muted">Revenue (month)</span><strong class="mono success">{{ data?.stats?.revenue_month }}</strong></div>
    </div>

    <div class="two">
      <div class="glass card">
        <div class="panel-h">
          <h3>Recent deposits</h3>
          <Button label="Manage" size="small" text @click="router.push('/admin/deposits')" />
        </div>
        <DataTable :value="data?.recent_deposits || []" size="small" class="p-datatable-sm">
          <Column field="user_email" header="User" />
          <Column field="display_label" header="Amount" />
          <Column header="Status">
            <template #body="{ data: r }"><Tag :value="r.status" :severity="statusSeverity(r.status)" /></template>
          </Column>
          <Column header="When">
            <template #body="{ data: r }">{{ shortDate(r.created_at) }}</template>
          </Column>
        </DataTable>
      </div>
      <div class="glass card">
        <div class="panel-h">
          <h3>Recent withdrawals</h3>
          <Button label="Manage" size="small" text @click="router.push('/admin/withdrawals')" />
        </div>
        <DataTable :value="data?.recent_withdrawals || []" size="small" class="p-datatable-sm">
          <Column field="user_email" header="User" />
          <Column field="display_label" header="Amount" />
          <Column header="Status">
            <template #body="{ data: r }"><Tag :value="r.status" :severity="statusSeverity(r.status)" /></template>
          </Column>
          <Column header="When">
            <template #body="{ data: r }">{{ shortDate(r.created_at) }}</template>
          </Column>
        </DataTable>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}
@media (max-width: 900px) { .grid-stats { grid-template-columns: 1fr 1fr; } }
.sums {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  padding: 1rem;
  margin-bottom: 1rem;
}
.sums > div { display: flex; flex-direction: column; gap: 0.25rem; }
@media (max-width: 800px) { .sums { grid-template-columns: 1fr 1fr; } }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 960px) { .two { grid-template-columns: 1fr; } }
.card { padding: 0.75rem; }
.panel-h { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; padding: 0 0.25rem; }
.success { color: var(--ci-success); }
</style>
