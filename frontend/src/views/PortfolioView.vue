<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Skeleton from 'primevue/skeleton'
import VueApexCharts from 'vue3-apexcharts'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import { api } from '@/services/api'
import { formatMoney } from '@/utils/money'
import type { PortfolioData } from '@/types/api'

const loading = ref(true)
const days = ref(30)
const data = ref<PortfolioData | null>(null)

const series = computed(() => [
  { name: 'Equity', data: data.value?.equity || [] },
  { name: 'Profit', data: data.value?.profit || [] },
])
const options = computed(() => ({
  chart: { type: 'area', toolbar: { show: false }, background: 'transparent', fontFamily: 'Inter, system-ui, sans-serif' },
  stroke: { curve: 'smooth', width: 2.5 },
  colors: ['#3B82F6', '#22C55E'],
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.3, opacityTo: 0.02 } },
  dataLabels: { enabled: false },
  xaxis: {
    categories: data.value?.labels || [],
    labels: { style: { colors: '#9CA3AF' }, hideOverlappingLabels: true },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: { labels: { style: { colors: '#9CA3AF' } } },
  grid: { borderColor: 'rgba(255,255,255,0.06)' },
  legend: { labels: { colors: '#9CA3AF' } },
  tooltip: { theme: 'dark' },
}))

async function load(d = days.value) {
  loading.value = true
  days.value = d
  try {
    const res = await api.portfolio(d)
    data.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(() => load(30))
</script>

<template>
  <div>
    <PageHeader title="Performance" subtitle="Portfolio equity over time">
      <Button label="7D" size="small" :outlined="days !== 7" @click="load(7)" />
      <Button label="30D" size="small" :outlined="days !== 30" @click="load(30)" />
      <Button label="90D" size="small" :outlined="days !== 90" @click="load(90)" />
    </PageHeader>

    <div v-if="loading" class="grid-stats">
      <Skeleton v-for="i in 3" :key="i" height="100px" border-radius="18px" />
    </div>
    <div v-else class="grid-stats">
      <StatCard label="Equity now" :value="formatMoney(data?.equity_now ?? 0)" icon="pi pi-chart-pie" />
      <StatCard label="Active investments" :value="String(data?.active_investments ?? 0)" icon="pi pi-briefcase" />
      <StatCard label="Total earned" :value="`+${formatMoney(data?.total_earned ?? 0)}`" icon="pi pi-dollar" tone="success" />
    </div>

    <div class="glass chart-card">
      <VueApexCharts v-if="data" type="area" height="320" :options="options" :series="series" />
      <p v-if="data?.disclaimer" class="muted small disclaimer">{{ data.disclaimer }}</p>
    </div>
  </div>
</template>

<style scoped>
.grid-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.85rem;
  margin-bottom: 1rem;
}
@media (max-width: 800px) { .grid-stats { grid-template-columns: 1fr; } }
.chart-card { padding: 1rem; }
.disclaimer { margin: 0.75rem 0 0; font-size: 0.78rem; }
</style>
