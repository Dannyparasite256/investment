<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api, unwrapList } from '@/services/api'
import { formatMoney, shortDate, statusSeverity } from '@/utils/money'
import type { Cryptocurrency, Deposit } from '@/types/api'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const rows = ref<Deposit[]>([])
const cryptos = ref<Cryptocurrency[]>([])
const loading = ref(true)
const open = ref(false)
const cryptoId = ref<number | null>(null)
const amount = ref<number | null>(null)
const txHash = ref('')
const submitting = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  try {
    const [d, c] = await Promise.all([api.deposits(), api.cryptocurrencies()])
    rows.value = unwrapList(d.data)
    cryptos.value = unwrapList(c.data as any)
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!cryptoId.value || !amount.value) return
  submitting.value = true
  error.value = ''
  try {
    const fd = new FormData()
    fd.append('cryptocurrency', String(cryptoId.value))
    fd.append('amount', String(amount.value))
    if (txHash.value) fd.append('transaction_hash', txHash.value)
    await api.createDeposit(fd)
    ui.toast('Deposit submitted', 'Awaiting admin approval.', 'success')
    open.value = false
    amount.value = null
    txHash.value = ''
    await load()
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Could not submit deposit'
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Deposits" subtitle="Crypto deposits credit after admin approval">
      <Button label="New deposit" icon="pi pi-plus" @click="open = true" />
    </PageHeader>
    <div class="glass panel">
      <DataTable v-if="rows.length" :value="rows" paginator :rows="10" :loading="loading">
        <Column field="created_at" header="Date">
          <template #body="{ data }">{{ shortDate(data.created_at) }}</template>
        </Column>
        <Column field="crypto_symbol" header="Asset" />
        <Column field="amount" header="Amount">
          <template #body="{ data }"><span class="mono">{{ formatMoney(data.amount, 8) }} {{ data.crypto_symbol }}</span></template>
        </Column>
        <Column field="status" header="Status">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column field="transaction_hash" header="Tx hash">
          <template #body="{ data }"><span class="mono muted small">{{ data.transaction_hash || '—' }}</span></template>
        </Column>
      </DataTable>
      <EmptyState v-else-if="!loading" title="No deposits yet" text="Submit a crypto deposit to fund your wallet.">
        <Button label="New deposit" icon="pi pi-plus" @click="open = true" />
      </EmptyState>
    </div>

    <Dialog v-model:visible="open" modal header="New deposit" :style="{ width: 'min(440px, 95vw)' }">
      <Message v-if="error" severity="error" class="mb" :closable="false">{{ error }}</Message>
      <div class="form">
        <label>
          <span>Cryptocurrency</span>
          <Select v-model="cryptoId" :options="cryptos" option-label="symbol" option-value="id" placeholder="Select asset" class="w-full" />
        </label>
        <label>
          <span>Amount</span>
          <InputNumber v-model="amount" mode="decimal" :min-fraction-digits="2" :max-fraction-digits="8" fluid />
        </label>
        <label>
          <span>Transaction hash (optional)</span>
          <InputText v-model="txHash" class="w-full" placeholder="0x… / on-chain hash" />
        </label>
        <Button label="Submit deposit" icon="pi pi-check" class="w-full" :loading="submitting" @click="submit" />
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
.panel { padding: 0.75rem; }
.form { display: grid; gap: 0.85rem; }
.form label { display: grid; gap: 0.35rem; }
.form span { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ci-muted); font-weight: 600; }
.w-full { width: 100%; }
.mb { margin-bottom: 0.75rem; }
.small { font-size: 0.78rem; }
</style>
