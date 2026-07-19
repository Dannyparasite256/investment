<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Skeleton from 'primevue/skeleton'
import VueApexCharts from 'vue3-apexcharts'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { useAuthStore } from '@/stores/auth'
import { useCurrencyStore } from '@/stores/currency'
import { api, unwrapList } from '@/services/api'
import { formatDisplay, formatMoney, shortDate, statusSeverity } from '@/utils/money'
import type { InvestmentPlan, Transaction, Earning } from '@/types/api'

const auth = useAuthStore()
const currency = useCurrencyStore()
const router = useRouter()
const loading = ref(true)
const plans = ref<InvestmentPlan[]>([])
const transactions = ref<Transaction[]>([])
const earnings = ref<Earning[]>([])
const prices = ref<Record<string, string | number>>({})

const available = computed(() => formatDisplay(currency.balances?.available) || formatMoney(auth.wallet?.available_balance ?? 0))
const profit = computed(() => formatDisplay(currency.balances?.profit) || formatMoney(auth.wallet?.total_profit ?? 0))
const invested = computed(() => formatDisplay((currency.balances as any)?.active_investments?.capital) || formatMoney(auth.wallet?.total_invested ?? 0))
const deposited = computed(() => formatMoney(auth.wallet?.total_deposited ?? 0))

const chartSeries = computed(() => [{
  name: 'Earnings',
  data: earnings.value.slice().reverse().map((e) => parseFloat(e.amount) || 0),
}])
const chartOptions = computed(() => ({
  chart: { type: 'area', toolbar: { show: false }, background: 'transparent', fontFamily: 'Inter, system-ui, sans-serif' },
  stroke: { curve: 'smooth', width: 2.5, colors: ['#3B82F6'] },
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.35, opacityTo: 0.02, stops: [0, 100] } },
  dataLabels: { enabled: false },
  xaxis: {
    categories: earnings.value.slice().reverse().map((e) => shortDate(e.created_at)),
    labels: { style: { colors: '#9CA3AF' }, hideOverlappingLabels: true },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: { labels: { style: { colors: '#9CA3AF' } } },
  grid: { borderColor: 'rgba(255,255,255,0.06)' },
  tooltip: { theme: 'dark' },
  legend: { show: false },
}))

onMounted(async () => {
  loading.value = true
  try {
    await auth.refreshWallet()
    if (!currency.balances) await currency.init()
    else await currency.refreshBalances()
    const [p, t, e, pr] = await Promise.allSettled([
      api.plans(),
      api.transactions({ page: 1 }),
      api.earnings(),
      api.prices(),
    ])
    if (p.status === 'fulfilled') plans.value = unwrapList(p.value.data).slice(0, 3)
    if (t.status === 'fulfilled') transactions.value = unwrapList(t.value.data).slice(0, 8)
    if (e.status === 'fulfilled') earnings.value = unwrapList(e.value.data).slice(0, 20)
    if (pr.status === 'fulfilled') prices.value = pr.value.data?.prices || {}
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="Dashboard" subtitle="Your portfolio at a glance">
      <Button label="Deposit" icon="pi pi-download" @click="router.push('/deposits')" />
      <Button label="Invest" icon="pi pi-chart-line" severity="secondary" outlined @click="router.push('/plans')" />
    </PageHeader>

    <div v-if="loading" class="grid-stats">
      <Skeleton v-for="i in 4" :key="i" height="110px" border-radius="18px" />
    </div>
    <div v-else class="grid-stats">
      <StatCard label="Available" :value="available" icon="pi pi-wallet" />
      <StatCard label="Total profit" :value="`+${profit}`" icon="pi pi-arrow-up-right" tone="success" />
      <StatCard label="Invested" :value="invested" icon="pi pi-briefcase" />
      <StatCard label="Deposited" :value="deposited" icon="pi pi-download" tone="gold" />
    </div>

    <div class="hero glass">
      <div>
        <div class="stat-label">Available balance</div>
        <div class="hero-val mono gradient-text">{{ available }}</div>
        <div class="muted small">
          Locked {{ formatDisplay(currency.balances?.locked) }} · Total {{ formatDisplay(currency.balances?.balance) }}
          · {{ currency.code || 'USD' }}
        </div>
      </div>
      <div class="actions">
        <Button label="Deposit" icon="pi pi-download" @click="router.push('/deposits')" />
        <Button label="Withdraw" icon="pi pi-upload" outlined @click="router.push('/withdrawals')" />
        <Button label="Invest" icon="pi pi-chart-line" text @click="router.push('/plans')" />
      </div>
    </div>

    <div class="ticker glass" v-if="Object.keys(prices).length">
      <span class="muted live"><i class="pi pi-circle-fill" /> Live</span>
      <span v-for="(v, k) in prices" :key="k" class="chip">
        {{ k }} <strong class="mono">${{ v }}</strong>
      </span>
      <Button label="Markets" size="small" text class="ms" @click="router.push('/markets')" />
    </div>

    <div class="two">
      <div class="glass panel">
        <div class="panel-h">
          <h3>Earnings</h3>
          <Button label="View all" size="small" text @click="router.push('/earnings')" />
        </div>
        <div class="chart-box">
          <VueApexCharts type="area" height="260" :options="chartOptions" :series="chartSeries" />
        </div>
      </div>
      <div class="glass panel">
        <div class="panel-h">
          <h3>Featured plans</h3>
          <Button label="Browse" size="small" text @click="router.push('/plans')" />
        </div>
        <div v-if="plans.length" class="plans">
          <button
            v-for="p in plans"
            :key="p.id"
            type="button"
            class="plan-row"
            @click="router.push(`/plans/${p.slug}`)"
          >
            <div>
              <strong>{{ p.name }}</strong>
              <div class="muted small">{{ p.duration_days }}d · {{ p.payout_frequency }}</div>
            </div>
            <div class="mono success">{{ p.expected_return || `${p.profit_rate_percent}%` }}</div>
          </button>
        </div>
        <EmptyState v-else title="No plans yet" text="Investment plans will appear here." />
      </div>
    </div>

    <div class="glass panel">
      <div class="panel-h">
        <h3>Recent transactions</h3>
        <Button label="History" size="small" text @click="router.push('/transactions')" />
      </div>
      <DataTable
        v-if="transactions.length"
        :value="transactions"
        size="small"
        :rows="8"
        class="p-datatable-sm"
      >
        <Column field="created_at" header="Date">
          <template #body="{ data }">{{ shortDate(data.created_at) }}</template>
        </Column>
        <Column field="tx_type" header="Type" />
        <Column field="description" header="Description" />
        <Column field="amount" header="Amount">
          <template #body="{ data }"><span class="mono">{{ formatMoney(data.amount) }}</span></template>
        </Column>
        <Column field="status" header="Status">
          <template #body="{ data }">
            <Tag :value="data.status" :severity="statusSeverity(data.status)" />
          </template>
        </Column>
      </DataTable>
      <EmptyState v-else title="No transactions yet" text="Deposits, investments, and payouts show up here.">
        <Button label="Make a deposit" icon="pi pi-download" @click="router.push('/deposits')" />
      </EmptyState>
    </div>
  </div>
</template>

<style scoped>
.hero {
  margin-top: 1rem;
  padding: 1.35rem 1.4rem;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  align-items: flex-end;
}
.hero-val {
  font-size: clamp(1.8rem, 4vw, 2.5rem);
  font-weight: 800;
  letter-spacing: -0.04em;
  margin: 0.25rem 0;
}
.actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.small { font-size: 0.82rem; }
.ticker {
  margin-top: 0.85rem;
  padding: 0.75rem 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  align-items: center;
}
.live { display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.8rem; }
.live i { font-size: 0.45rem; color: #22C55E; }
.chip {
  padding: 0.35rem 0.65rem;
  border-radius: 10px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--ci-border);
  font-size: 0.82rem;
}
.ms { margin-left: auto; }
.two {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 1rem;
  margin-top: 1rem;
}
@media (max-width: 900px) {
  .two { grid-template-columns: 1fr; }
}
.panel {
  margin-top: 1rem;
  padding: 1rem 1.1rem 1.15rem;
}
.panel-h {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.panel-h h3 { font-size: 1rem; font-weight: 700; }
.chart-box { height: 260px; }
.chart { height: 100%; }
.plans { display: grid; gap: 0.45rem; }
.plan-row {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  width: 100%;
  text-align: left;
  border: 1px solid var(--ci-border);
  background: rgba(255,255,255,0.03);
  color: var(--ci-text);
  border-radius: 12px;
  padding: 0.75rem 0.85rem;
  cursor: pointer;
}
.plan-row:hover {
  border-color: rgba(59, 130, 246, 0.4);
}
</style>
