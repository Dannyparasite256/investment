<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import VueApexCharts from 'vue3-apexcharts'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api, unwrapList } from '@/services/api'
import { formatMoney, shortDate } from '@/utils/money'
import type { Earning } from '@/types/api'

const router = useRouter()
const rows = ref<Earning[]>([])
const loading = ref(true)

const series = computed(() => [{
  name: 'Earnings',
  data: rows.value.slice().reverse().map((e) => parseFloat(e.amount) || 0),
}])
const chartOptions = computed(() => ({
  chart: { type: 'area', toolbar: { show: false }, background: 'transparent' },
  stroke: { curve: 'smooth', width: 2.5, colors: ['#3B82F6'] },
  fill: {
    type: 'gradient',
    gradient: { shadeIntensity: 1, opacityFrom: 0.35, opacityTo: 0.02, stops: [0, 100] },
  },
  dataLabels: { enabled: false },
  xaxis: {
    categories: rows.value.slice().reverse().map((e) => shortDate(e.created_at)),
    labels: { style: { colors: '#9CA3AF' }, rotate: 0, hideOverlappingLabels: true },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: { labels: { style: { colors: '#9CA3AF' } } },
  grid: { borderColor: 'rgba(255,255,255,0.06)' },
  tooltip: { theme: 'dark' },
}))

onMounted(async () => {
  try {
    const { data } = await api.earnings()
    rows.value = unwrapList(data)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="Earnings" subtitle="Payout history across investments" />
    <div class="glass panel chart" v-if="rows.length">
      <VueApexCharts type="area" height="280" :options="chartOptions" :series="series" />
    </div>
    <div class="glass panel">
      <DataTable v-if="rows.length" :value="rows" paginator :rows="12" :loading="loading">
        <Column field="created_at" header="Date">
          <template #body="{ data }">{{ shortDate(data.created_at) }}</template>
        </Column>
        <Column field="period_number" header="Period" />
        <Column field="amount" header="Amount">
          <template #body="{ data }"><span class="mono success">+{{ formatMoney(data.amount) }}</span></template>
        </Column>
        <Column field="is_reinvested" header="Reinvested">
          <template #body="{ data }">{{ data.is_reinvested ? 'Yes' : 'No' }}</template>
        </Column>
        <Column header="" style="width:7rem">
          <template #body="{ data }">
            <Button
              label="Receipt"
              size="small"
              text
              icon="pi pi-file"
              @click="router.push(`/receipts/earning/${data.id}`)"
            />
          </template>
        </Column>
      </DataTable>
      <EmptyState v-else-if="!loading" title="No earnings yet" text="Profits will show as your investments pay out." />
    </div>
  </div>
</template>

<style scoped>
.panel { padding: 0.85rem; margin-bottom: 1rem; }
.chart { padding-bottom: 0.25rem; }
</style>
