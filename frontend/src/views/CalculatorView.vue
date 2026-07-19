<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Button from 'primevue/button'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { formatMoney } from '@/utils/money'
import { useRouter } from 'vue-router'

const router = useRouter()
const plans = ref<any[]>([])
const planId = ref<string | null>(null)
const amount = ref(100)
const result = ref<{ estimated_profit: string; estimated_total: string } | null>(null)
const loading = ref(false)

const selected = computed(() => plans.value.find((p) => p.id === planId.value) || null)

async function load() {
  const { data } = await api.calculatorPlans()
  plans.value = data.plans || []
  if (plans.value.length) planId.value = plans.value[0].id
}

async function calc() {
  if (!selected.value) return
  loading.value = true
  try {
    const { data } = await api.calculate({
      amount: amount.value,
      profit_rate_percent: selected.value.profit_rate_percent,
      duration_days: selected.value.duration_days,
    })
    result.value = data as any
  } finally {
    loading.value = false
  }
}

watch([planId, amount], () => { if (selected.value) calc() })
onMounted(async () => { await load(); await calc() })
</script>

<template>
  <div>
    <PageHeader title="Return calculator" subtitle="Estimate profits before you invest" />
    <div class="grid">
      <div class="glass card">
        <label>Plan
          <Select
            v-model="planId"
            :options="plans"
            option-label="name"
            option-value="id"
            class="w-full"
          />
        </label>
        <label class="mt">Amount
          <InputNumber v-model="amount" mode="decimal" :min-fraction-digits="0" :max-fraction-digits="8" class="w-full" />
        </label>
        <div v-if="selected" class="meta muted small mt">
          Rate {{ selected.profit_rate_percent }}% · {{ selected.duration_days }} days · {{ selected.payout_frequency }}
          <div>Range {{ selected.min_deposit }} – {{ selected.max_deposit }}</div>
        </div>
        <Button label="Recalculate" icon="pi pi-refresh" class="mt" :loading="loading" @click="calc" />
        <Button
          v-if="selected"
          label="Invest in this plan"
          icon="pi pi-chart-line"
          class="mt"
          outlined
          @click="router.push(`/plans/${selected.slug}`)"
        />
      </div>
      <div class="glass card result">
        <div class="stat-label">Estimated profit</div>
        <div class="big mono success">+{{ formatMoney(result?.estimated_profit ?? 0) }}</div>
        <div class="stat-label mt">Estimated total</div>
        <div class="mid mono">{{ formatMoney(result?.estimated_total ?? 0) }}</div>
        <p class="muted small mt">Illustrative only. Actual returns depend on plan rules and market conditions.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 800px) { .grid { grid-template-columns: 1fr; } }
.card { padding: 1.15rem; display: flex; flex-direction: column; }
label { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 600; font-size: 0.85rem; color: var(--ci-muted); }
.mt { margin-top: 0.85rem; }
.big { font-size: 2rem; font-weight: 800; }
.mid { font-size: 1.35rem; font-weight: 700; }
.success { color: var(--ci-success); }
.small { font-size: 0.82rem; }
:deep(.p-inputnumber) { width: 100%; }
</style>
