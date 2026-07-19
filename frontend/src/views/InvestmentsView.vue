<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'
import Skeleton from 'primevue/skeleton'
import Button from 'primevue/button'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api, unwrapList } from '@/services/api'
import { formatMoney, shortDate, statusSeverity } from '@/utils/money'
import type { Investment } from '@/types/api'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(true)
const rows = ref<Investment[]>([])

onMounted(async () => {
  try {
    const { data } = await api.investments()
    rows.value = unwrapList(data)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="My investments" subtitle="Active and completed positions">
      <Button label="New investment" icon="pi pi-plus" @click="router.push('/plans')" />
    </PageHeader>
    <div class="glass panel">
      <Skeleton v-if="loading" height="240px" />
      <DataTable
        v-else-if="rows.length"
        :value="rows"
        paginator
        :rows="10"
        responsive-layout="scroll"
        row-hover
        @row-click="(e: any) => router.push(`/investments/${e.data.id}`)"
      >
        <Column field="plan_name" header="Plan" />
        <Column field="amount" header="Amount">
          <template #body="{ data }"><span class="mono">{{ formatMoney(data.amount) }}</span></template>
        </Column>
        <Column field="total_earned" header="Earned">
          <template #body="{ data }"><span class="mono success">+{{ formatMoney(data.total_earned) }}</span></template>
        </Column>
        <Column header="Progress">
          <template #body="{ data }">
            <ProgressBar :value="Math.min(100, data.progress_percent || 0)" style="height:8px" />
            <div class="muted small">{{ Math.round(data.progress_percent || 0) }}%</div>
          </template>
        </Column>
        <Column field="status" header="Status">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column field="matures_at" header="Matures">
          <template #body="{ data }">{{ shortDate(data.matures_at) }}</template>
        </Column>
      </DataTable>
      <EmptyState v-else title="No investments yet" text="Browse plans and put your balance to work.">
        <Button label="Browse plans" icon="pi pi-chart-line" @click="router.push('/plans')" />
      </EmptyState>
    </div>
  </div>
</template>

<style scoped>
.panel { padding: 0.75rem; }
.small { font-size: 0.75rem; margin-top: 0.2rem; }
:deep(.p-datatable-tbody > tr) { cursor: pointer; }
</style>
