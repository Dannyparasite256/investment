<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Select from 'primevue/select'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import { useAuthStore } from '@/stores/auth'
import { useCurrencyStore } from '@/stores/currency'
import { formatDisplay, formatMoney } from '@/utils/money'
import { useUiStore } from '@/stores/ui'

const auth = useAuthStore()
const currency = useCurrencyStore()
const router = useRouter()
const ui = useUiStore()

onMounted(async () => {
  await auth.refreshWallet()
  if (!currency.options.length) await currency.init()
  else await currency.refreshBalances()
})

async function onCurrency(code: string) {
  const ok = await currency.setCurrency(code)
  if (ok) ui.toast('Currency', `Showing balances in ${code}`, 'success')
}
</script>

<template>
  <div>
    <PageHeader title="Wallet" subtitle="Balances in your display currency (live rates)">
      <Select
        :model-value="currency.code"
        :options="currency.options"
        option-label="label"
        option-value="code"
        placeholder="Currency"
        class="fx"
        :loading="currency.switching"
        @update:model-value="onCurrency"
      />
      <Button label="Deposit" icon="pi pi-download" @click="router.push('/deposits')" />
      <Button label="Withdraw" icon="pi pi-upload" outlined @click="router.push('/withdrawals')" />
    </PageHeader>
    <div class="grid-stats">
      <StatCard label="Balance" :value="formatDisplay(currency.balances?.balance)" icon="pi pi-wallet" />
      <StatCard label="Available" :value="formatDisplay(currency.balances?.available)" icon="pi pi-check-circle" tone="success" />
      <StatCard label="Locked" :value="formatDisplay(currency.balances?.locked)" icon="pi pi-lock" />
      <StatCard label="Profit" :value="formatDisplay(currency.balances?.profit)" icon="pi pi-chart-line" tone="gold" />
    </div>
    <div class="glass panel">
      <h3>Summary · {{ currency.code || 'USD' }}</h3>
      <p class="muted small">
        Converted with live rates. Platform ledger is USD-equivalent.
        <span v-if="currency.balances?.available?.usd_equivalent">
          Available ≈ ${{ currency.balances.available.usd_equivalent }} USD
        </span>
      </p>
      <ul>
        <li>
          <span>Active capital</span>
          <strong class="mono">{{ formatDisplay((currency.balances as any)?.active_investments?.capital || currency.balances?.active_capital) }}</strong>
        </li>
        <li>
          <span>Referral earnings</span>
          <strong class="mono success">{{ formatDisplay(currency.balances?.referral) }}</strong>
        </li>
        <li>
          <span>Total deposited (platform)</span>
          <strong class="mono">{{ formatMoney(auth.wallet?.total_deposited ?? 0) }} USD-eq</strong>
        </li>
        <li>
          <span>Total withdrawn (platform)</span>
          <strong class="mono">{{ formatMoney(auth.wallet?.total_withdrawn ?? 0) }} USD-eq</strong>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.fx { min-width: 10rem; }
.grid-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}
@media (max-width: 900px) { .grid-stats { grid-template-columns: 1fr 1fr; } }
.panel { margin-top: 1rem; padding: 1.15rem; }
h3 { margin-bottom: 0.35rem; font-size: 1rem; }
.small { font-size: 0.85rem; margin-bottom: 0.75rem; }
ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.45rem; }
li {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.65rem 0.75rem;
  border-radius: 12px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--ci-border);
}
li span { color: var(--ci-muted); }
.success { color: var(--ci-success); }
</style>
