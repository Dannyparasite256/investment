<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import { api } from '@/services/api'
import { formatMoney } from '@/utils/money'

const data = ref<any>(null)
onMounted(async () => {
  const res = await api.trust()
  data.value = res.data
})
</script>

<template>
  <div>
    <PageHeader title="Trust center" subtitle="Transparent platform activity (last 30 days)" />
    <div v-if="data" class="grid">
      <StatCard label="Withdrawals paid" :value="String(data.withdrawals_paid_count)" icon="pi pi-send" />
      <StatCard label="Paid volume" :value="formatMoney(data.withdrawals_paid_volume)" icon="pi pi-dollar" />
      <StatCard label="Deposits approved" :value="String(data.deposits_approved_count)" icon="pi pi-check" />
      <StatCard label="Active investors" :value="String(data.active_investors)" icon="pi pi-users" />
    </div>
    <div class="glass note">
      <p>{{ data?.disclaimer }}</p>
      <p class="muted small">Pending withdrawals in queue: {{ data?.pending_withdrawals ?? '—' }}</p>
    </div>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
.note { padding: 1.1rem; border-radius: 16px; line-height: 1.5; }
.small { font-size: 0.85rem; }
</style>
