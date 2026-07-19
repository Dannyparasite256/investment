<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import PageHeader from '@/components/ui/PageHeader.vue'
import CryptoLabel from '@/components/ui/CryptoLabel.vue'
import { api } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const rows = ref<any[]>([])
const loading = ref(true)
const q = ref('')
const status = ref('pending')
const busy = ref('')

const statuses = [
  { label: 'Pending', value: 'pending' },
  { label: 'Approved', value: 'approved' },
  { label: 'All', value: '' },
  { label: 'Paid', value: 'paid' },
  { label: 'Rejected', value: 'rejected' },
]

async function load() {
  loading.value = true
  try {
    const { data } = await api.staffWithdrawals({ status: status.value || undefined, q: q.value || undefined })
    rows.value = data.results || []
  } finally {
    loading.value = false
  }
}

async function act(id: string, action: 'approve' | 'paid' | 'reject') {
  busy.value = id + action
  try {
    const payload =
      action === 'reject' ? { reason: 'Rejected by staff' }
        : action === 'paid' ? { tx_hash: '' }
          : { notes: '' }
    const { data } = await api.staffWithdrawalAction(id, action, payload)
    if (data.ok) {
      ui.toast('Done', `Withdrawal ${action}`, 'success')
      await load()
    } else ui.toast('Failed', data.detail || 'Failed', 'error')
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Failed', 'error')
  } finally {
    busy.value = ''
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Admin · Withdrawals" subtitle="Approve, mark paid, or reject">
      <Select v-model="status" :options="statuses" option-label="label" option-value="value" @change="load" />
      <InputText v-model="q" placeholder="Search" @keyup.enter="load" />
      <Button icon="pi pi-search" @click="load" />
    </PageHeader>
    <div class="glass card">
      <DataTable :value="rows" :loading="loading" paginator :rows="15" class="p-datatable-sm">
        <Column field="user_email" header="User" />
        <Column field="display_label" header="Amount" />
        <Column field="crypto_symbol" header="Asset" style="width:9rem">
          <template #body="{ data }">
            <CryptoLabel :symbol="data.crypto_symbol" size="sm" />
          </template>
        </Column>
        <Column field="wallet_address" header="Address">
          <template #body="{ data }"><span class="mono small">{{ data.wallet_address?.slice(0, 18) }}…</span></template>
        </Column>
        <Column header="Status" style="width:7rem">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column header="When" style="width:8rem">
          <template #body="{ data }">{{ shortDate(data.created_at) }}</template>
        </Column>
        <Column header="Actions" style="width:14rem">
          <template #body="{ data }">
            <div class="acts">
              <Button v-if="data.status==='pending'" label="Approve" size="small" :loading="busy===data.id+'approve'" @click="act(data.id,'approve')" />
              <Button v-if="data.status==='approved' || data.status==='pending'" label="Paid" size="small" severity="success" :loading="busy===data.id+'paid'" @click="act(data.id,'paid')" />
              <Button v-if="['pending','approved'].includes(data.status)" label="Reject" size="small" severity="danger" outlined :loading="busy===data.id+'reject'" @click="act(data.id,'reject')" />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 0.5rem; }
.acts { display: flex; gap: 0.3rem; flex-wrap: wrap; }
.small { font-size: 0.78rem; }
</style>
