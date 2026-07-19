<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import InputNumber from 'primevue/inputnumber'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Skeleton from 'primevue/skeleton'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { formatMoney } from '@/utils/money'
import type { InvestmentPlan } from '@/types/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const ui = useUiStore()

const plan = ref<InvestmentPlan | null>(null)
const amount = ref<number | null>(null)
const autoReinvest = ref(false)
const loading = ref(true)
const submitting = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    const { data } = await api.plan(String(route.params.slug))
    plan.value = data
    amount.value = parseFloat(data.min_deposit) || null
  } catch {
    error.value = 'Plan not found'
  } finally {
    loading.value = false
  }
})

async function invest() {
  if (!plan.value || !amount.value) return
  submitting.value = true
  error.value = ''
  try {
    await api.createInvestment({
      plan_id: plan.value.id,
      amount: amount.value,
      auto_reinvest: autoReinvest.value,
    })
    await auth.refreshWallet()
    ui.toast('Investment created', 'Your plan is now active.', 'success')
    router.push('/investments')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Could not create investment'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader :title="plan?.name || 'Plan'" subtitle="Review terms and invest">
      <Button label="Back" icon="pi pi-arrow-left" text @click="router.push('/plans')" />
    </PageHeader>

    <Skeleton v-if="loading" height="360px" border-radius="18px" />
    <div v-else-if="plan" class="layout">
      <div class="glass info">
        <div class="roi mono gradient-text">{{ plan.expected_return || `${plan.profit_rate_percent}%` }}</div>
        <p class="muted">{{ plan.description || plan.short_description }}</p>
        <ul>
          <li><span>Duration</span><strong>{{ plan.duration_days }} days</strong></li>
          <li><span>Payout</span><strong>{{ plan.payout_frequency }}</strong></li>
          <li><span>Risk</span><strong>{{ plan.risk_level }}</strong></li>
          <li><span>Min / Max</span><strong class="mono">{{ formatMoney(plan.min_deposit) }} – {{ formatMoney(plan.max_deposit) }}</strong></li>
          <li><span>Return principal</span><strong>{{ plan.return_principal ? 'Yes' : 'No' }}</strong></li>
        </ul>
      </div>
      <div class="glass form">
        <h3>Invest</h3>
        <p class="muted small">Available: <span class="mono">{{ formatMoney(auth.wallet?.available_balance ?? 0) }}</span></p>
        <Message v-if="error" severity="error" :closable="false" class="mb">{{ error }}</Message>
        <label class="field">
          <span>Amount</span>
          <InputNumber v-model="amount" mode="decimal" :min-fraction-digits="2" :max-fraction-digits="8" fluid />
        </label>
        <label class="check">
          <Checkbox v-model="autoReinvest" binary />
          <span>Auto-reinvest when allowed</span>
        </label>
        <Button label="Confirm investment" icon="pi pi-check" class="w-full" :loading="submitting" @click="invest" />
      </div>
    </div>
    <Message v-else severity="warn">{{ error || 'Plan unavailable' }}</Message>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 1rem;
}
@media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }
.info, .form { padding: 1.25rem; }
.roi { font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem; }
ul { list-style: none; padding: 0; margin: 1rem 0 0; display: grid; gap: 0.45rem; }
li {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.55rem 0.65rem;
  border-radius: 10px;
  background: rgba(255,255,255,0.03);
  font-size: 0.9rem;
}
li span { color: var(--ci-muted); }
.form h3 { margin-bottom: 0.35rem; }
.field { display: grid; gap: 0.35rem; margin: 0.85rem 0; }
.field span { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ci-muted); font-weight: 600; }
.check { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; font-size: 0.9rem; }
.w-full { width: 100%; }
.mb { margin-bottom: 0.75rem; }
.small { font-size: 0.85rem; }
</style>
