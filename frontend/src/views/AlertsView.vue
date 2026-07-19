<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api } from '@/services/api'
import { formatMoney, shortDate } from '@/utils/money'
import { useUiStore } from '@/stores/ui'
import type { PriceAlert } from '@/types/api'

const ui = useUiStore()
const alerts = ref<PriceAlert[]>([])
const loading = ref(true)
const form = ref({
  symbol: 'FX:EURUSD',
  label: '',
  target_price: 1.1,
  direction: 'above',
})
const directions = [
  { label: 'Above', value: 'above' },
  { label: 'Below', value: 'below' },
]

async function load() {
  loading.value = true
  try {
    const { data } = await api.alerts()
    alerts.value = Array.isArray(data) ? data : []
  } finally {
    loading.value = false
  }
}

async function create() {
  try {
    await api.createAlert({
      symbol: form.value.symbol,
      label: form.value.label,
      target_price: form.value.target_price,
      direction: form.value.direction,
    })
    ui.toast('Created', 'Price alert saved', 'success')
    await load()
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Could not create alert', 'error')
  }
}

async function remove(id: string) {
  await api.deleteAlert(id)
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Price alerts" subtitle="Get notified when a market hits your target" />
    <div class="glass card form">
      <InputText v-model="form.symbol" placeholder="Symbol" />
      <InputText v-model="form.label" placeholder="Label" />
      <InputNumber v-model="form.target_price" mode="decimal" :min-fraction-digits="2" :max-fraction-digits="8" />
      <Select v-model="form.direction" :options="directions" option-label="label" option-value="value" />
      <Button label="Add alert" icon="pi pi-bell" @click="create" />
    </div>
    <div class="glass card">
      <EmptyState v-if="!loading && !alerts.length" title="No alerts" text="Create an alert for FX or crypto prices." />
      <ul v-else class="list">
        <li v-for="a in alerts" :key="a.id">
          <div>
            <strong class="mono">{{ a.symbol }}</strong>
            <span class="muted"> {{ a.direction }} {{ formatMoney(a.target_price, 4) }}</span>
            <div class="muted small">{{ a.label || '—' }} · {{ shortDate(a.created_at) }}</div>
          </div>
          <div class="row">
            <Tag :value="a.is_active ? 'Active' : 'Off'" :severity="a.is_active ? 'success' : 'secondary'" />
            <Button icon="pi pi-trash" text severity="danger" @click="remove(a.id)" />
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 1rem; margin-bottom: 0.85rem; }
.form { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.list { list-style: none; margin: 0; padding: 0; }
.list li {
  display: flex; justify-content: space-between; gap: 0.75rem; align-items: center;
  padding: 0.75rem 0; border-bottom: 1px solid var(--ci-border);
}
.row { display: flex; align-items: center; gap: 0.35rem; }
.small { font-size: 0.8rem; }
</style>
