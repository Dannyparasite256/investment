<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import PageHeader from '@/components/ui/PageHeader.vue'
import CryptoIcon from '@/components/ui/CryptoIcon.vue'
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
  { label: 'Queue (pending)', value: 'pending' },
  { label: 'All', value: '' },
  { label: 'Approved', value: 'approved' },
  { label: 'Rejected', value: 'rejected' },
]

async function load() {
  loading.value = true
  try {
    const { data } = await api.staffDeposits({ status: status.value || undefined, q: q.value || undefined })
    rows.value = data.results || []
  } finally {
    loading.value = false
  }
}

async function act(id: string, action: 'approve' | 'reject') {
  busy.value = id + action
  try {
    const payload = action === 'reject' ? { reason: 'Rejected by staff' } : { notes: '' }
    const { data } = await api.staffDepositAction(id, action, payload)
    if (data.ok) {
      ui.toast('Done', `Deposit ${action}d`, 'success')
      await load()
    } else {
      ui.toast('Failed', data.detail || 'Action failed', 'error')
    }
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Action failed', 'error')
  } finally {
    busy.value = ''
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Admin · Deposits" subtitle="Approve or reject user deposits">
      <Select v-model="status" :options="statuses" option-label="label" option-value="value" @change="load" />
      <InputText v-model="q" placeholder="Search email / hash" @keyup.enter="load" />
      <Button icon="pi pi-search" @click="load" />
    </PageHeader>
    <div class="glass card">
      <DataTable :value="rows" :loading="loading" paginator :rows="15" class="p-datatable-sm">
        <Column field="user_email" header="User" />
        <Column field="display_label" header="Amount" />
        <Column field="crypto_symbol" header="Asset" style="width:8rem">
          <template #body="{ data }">
            <span class="asset-cell">
              <CryptoIcon :symbol="data.crypto_symbol" size="sm" />
              <span>{{ data.crypto_symbol }}</span>
            </span>
          </template>
        </Column>
        <Column header="Status" style="width:7rem">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column header="When" style="width:8rem">
          <template #body="{ data }">{{ shortDate(data.created_at) }}</template>
        </Column>
        <Column header="Actions" style="width:12rem">
          <template #body="{ data }">
            <div v-if="['pending','waiting_confirmation'].includes(data.status)" class="acts">
              <Button label="Approve" size="small" :loading="busy===data.id+'approve'" @click="act(data.id,'approve')" />
              <Button label="Reject" size="small" severity="danger" outlined :loading="busy===data.id+'reject'" @click="act(data.id,'reject')" />
            </div>
            <span v-else class="muted">—</span>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 0.5rem; }
.acts { display: flex; gap: 0.35rem; flex-wrap: wrap; }
.asset-cell { display: inline-flex; align-items: center; gap: 0.4rem; }
</style>
