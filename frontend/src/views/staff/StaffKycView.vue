<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const rows = ref<any[]>([])
const loading = ref(true)
const busy = ref('')

async function load() {
  loading.value = true
  try {
    const { data } = await api.staffKyc()
    rows.value = data.results || []
  } finally {
    loading.value = false
  }
}

async function act(id: string, action: 'approve' | 'reject') {
  busy.value = id + action
  try {
    await api.staffKycAction(id, action, action === 'reject' ? { reason: 'Documents unclear' } : {})
    ui.toast('Done', `KYC ${action}d`, 'success')
    await load()
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
    <PageHeader title="Admin · KYC" subtitle="Identity verification queue" />
    <div class="glass card">
      <DataTable :value="rows" :loading="loading" paginator :rows="15" class="p-datatable-sm">
        <Column field="user_email" header="User" />
        <Column field="document_type" header="Type" />
        <Column field="document_number" header="Number" />
        <Column header="Status">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column header="When">
          <template #body="{ data }">{{ shortDate(data.created_at) }}</template>
        </Column>
        <Column header="Actions">
          <template #body="{ data }">
            <div class="acts">
              <Button label="Approve" size="small" :loading="busy===data.id+'approve'" @click="act(data.id,'approve')" />
              <Button label="Reject" size="small" severity="danger" outlined :loading="busy===data.id+'reject'" @click="act(data.id,'reject')" />
              <Button v-if="data.front_image" as="a" :href="data.front_image" target="_blank" label="Doc" size="small" text />
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
</style>
