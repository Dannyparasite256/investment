<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import PageHeader from '@/components/ui/PageHeader.vue'
import StatCard from '@/components/ui/StatCard.vue'
import { useAuthStore } from '@/stores/auth'
import { formatMoney } from '@/utils/money'

const auth = useAuthStore()
const router = useRouter()
onMounted(() => auth.refreshWallet())
</script>

<template>
  <div>
    <PageHeader title="Wallet" subtitle="Balances and capital allocation">
      <Button label="Deposit" icon="pi pi-download" @click="router.push('/deposits')" />
      <Button label="Withdraw" icon="pi pi-upload" outlined @click="router.push('/withdrawals')" />
    </PageHeader>
    <div class="grid-stats">
      <StatCard label="Balance" :value="formatMoney(auth.wallet?.balance ?? 0)" icon="pi pi-wallet" />
      <StatCard label="Available" :value="formatMoney(auth.wallet?.available_balance ?? 0)" icon="pi pi-check-circle" tone="success" />
      <StatCard label="Locked" :value="formatMoney(auth.wallet?.locked_balance ?? 0)" icon="pi pi-lock" />
      <StatCard label="Profit" :value="`+${formatMoney(auth.wallet?.total_profit ?? 0)}`" icon="pi pi-chart-line" tone="gold" />
    </div>
    <div class="glass panel">
      <h3>Summary</h3>
      <ul>
        <li><span>Total deposited</span><strong class="mono">{{ formatMoney(auth.wallet?.total_deposited ?? 0) }}</strong></li>
        <li><span>Total withdrawn</span><strong class="mono">{{ formatMoney(auth.wallet?.total_withdrawn ?? 0) }}</strong></li>
        <li><span>Total invested</span><strong class="mono">{{ formatMoney(auth.wallet?.total_invested ?? 0) }}</strong></li>
        <li><span>Referral earnings</span><strong class="mono success">+{{ formatMoney(auth.user?.referral_earnings ?? 0) }}</strong></li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.panel { margin-top: 1rem; padding: 1.15rem; }
h3 { margin-bottom: 0.75rem; font-size: 1rem; }
ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.45rem; }
li {
  display: flex;
  justify-content: space-between;
  padding: 0.65rem 0.75rem;
  border-radius: 12px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--ci-border);
}
li span { color: var(--ci-muted); }
</style>
