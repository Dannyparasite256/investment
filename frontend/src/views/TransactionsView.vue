<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import Button from 'primevue/button'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api, unwrapList } from '@/services/api'
import { formatMoney, shortDate, statusSeverity } from '@/utils/money'
import type { Transaction } from '@/types/api'

const router = useRouter()
const rows = ref<Transaction[]>([])
const loading = ref(true)
const type = ref<string | null>(null)
const types = [
  { label: 'All types', value: null },
  { label: 'Deposit', value: 'deposit' },
  { label: 'Withdrawal', value: 'withdrawal' },
  { label: 'Investment', value: 'investment' },
  { label: 'Profit', value: 'profit' },
  { label: 'Referral', value: 'referral' },
]

function openReceipt(tx: Transaction) {
  // Prefer domain receipts when the ledger points at a known object
  const refType = (tx as any).reference_type as string | undefined
  const refId = (tx as any).reference_id as string | undefined
  if (refType === 'investment' && refId) {
    router.push(`/receipts/investment/${refId}`)
    return
  }
  if (refType === 'earning' && refId) {
    router.push(`/receipts/earning/${refId}`)
    return
  }
  if ((refType === 'referral' || tx.tx_type === 'referral') && refId) {
    router.push(`/receipts/referral/${refId}`)
    return
  }
  if (refType === 'deposit' && refId) {
    router.push(`/receipts/deposit/${refId}`)
    return
  }
  if (refType === 'withdrawal' && refId) {
    router.push(`/receipts/withdrawal/${refId}`)
    return
  }
  router.push(`/receipts/transaction/${tx.id}`)
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.transactions({ tx_type: type.value || undefined })
    rows.value = unwrapList(data)
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  const header = 'date,type,amount,status,description\n'
  const body = rows.value.map((r) =>
    [r.created_at, r.tx_type, r.amount, r.status, `"${(r.description || '').replace(/"/g, '""')}"`].join(','),
  ).join('\n')
  const blob = new Blob([header + body], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'transactions.csv'
  a.click()
  URL.revokeObjectURL(url)
}

watch(type, load)
onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Transactions" subtitle="Full ledger history">
      <Select v-model="type" :options="types" option-label="label" option-value="value" class="filter" />
      <Button label="Export CSV" icon="pi pi-download" outlined @click="exportCsv" />
    </PageHeader>
    <div class="glass panel">
      <DataTable v-if="rows.length || loading" :value="rows" paginator :rows="15" :loading="loading" responsive-layout="scroll">
        <Column field="created_at" header="Date" sortable>
          <template #body="{ data }">{{ shortDate(data.created_at) }}</template>
        </Column>
        <Column field="tx_type" header="Type" sortable />
        <Column field="description" header="Description" />
        <Column field="amount" header="Amount" sortable>
          <template #body="{ data }"><span class="mono">{{ formatMoney(data.amount) }}</span></template>
        </Column>
        <Column field="status" header="Status">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column header="" style="width:7rem">
          <template #body="{ data }">
            <Button label="Receipt" size="small" text icon="pi pi-file" @click="openReceipt(data)" />
          </template>
        </Column>
      </DataTable>
      <EmptyState v-else title="No transactions" text="Activity will appear here as you use the platform." />
    </div>
  </div>
</template>

<style scoped>
.panel { padding: 0.75rem; }
.filter { min-width: 150px; }
</style>
