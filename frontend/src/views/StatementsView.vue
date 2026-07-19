<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { formatMoney, shortDate, statusSeverity } from '@/utils/money'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const loading = ref(true)
const exporting = ref<'csv' | 'pdf' | null>(null)
const txs = ref<any[]>([])
const generated = ref('')

onMounted(async () => {
  try {
    const { data } = await api.statements()
    txs.value = data.transactions || []
    generated.value = data.generated_at || ''
  } finally {
    loading.value = false
  }
})

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function exportCsvLocal() {
  const header = 'Date,Type,Amount,Status,Description\n'
  const rows = txs.value.map((t) =>
    [t.created_at, t.tx_type, t.amount, t.status, `"${(t.description || '').replace(/"/g, '""')}"`].join(','),
  ).join('\n')
  downloadBlob(new Blob([header + rows], { type: 'text/csv' }), 'statement.csv')
  ui.toast('Exported', 'CSV downloaded', 'success')
}

async function exportServer(fmt: 'csv' | 'pdf') {
  exporting.value = fmt
  try {
    const { data } = await api.statements({ format: fmt })
    const blob = data instanceof Blob
      ? data
      : new Blob([data as any], { type: fmt === 'pdf' ? 'application/pdf' : 'text/csv' })
    downloadBlob(blob, fmt === 'pdf' ? 'statement.pdf' : 'statement.csv')
    ui.toast('Exported', `${fmt.toUpperCase()} downloaded`, 'success')
  } catch (e: any) {
    if (fmt === 'csv') {
      exportCsvLocal()
      return
    }
    ui.toast('Export failed', e?.response?.data?.detail || 'Could not generate PDF', 'error')
  } finally {
    exporting.value = null
  }
}
</script>

<template>
  <div>
    <PageHeader title="Statements" :subtitle="generated ? `Generated ${shortDate(generated)}` : 'Account statement export'">
      <Button
        label="Export CSV"
        icon="pi pi-download"
        outlined
        :loading="exporting === 'csv'"
        :disabled="loading || !!exporting"
        @click="exportServer('csv')"
      />
      <Button
        label="Export PDF"
        icon="pi pi-file-pdf"
        :loading="exporting === 'pdf'"
        :disabled="loading || !!exporting"
        @click="exportServer('pdf')"
      />
    </PageHeader>
    <div class="glass card">
      <DataTable :value="txs" :loading="loading" paginator :rows="15" class="p-datatable-sm">
        <Column header="Date" style="width:9rem">
          <template #body="{ data }">{{ shortDate(data.created_at) }}</template>
        </Column>
        <Column field="tx_type" header="Type" style="width:7rem" />
        <Column header="Amount" style="width:8rem">
          <template #body="{ data }"><span class="mono">{{ formatMoney(data.amount) }}</span></template>
        </Column>
        <Column header="Status" style="width:7rem">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column field="description" header="Description" />
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 0.5rem; border-radius: 18px; overflow: hidden; }
</style>
