<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'

const rows = ref<any[]>([])
const loading = ref(true)
onMounted(async () => {
  try {
    const { data } = await api.staffFraud()
    rows.value = data.results || []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="Fraud signals" subtitle="Heuristic risk flags (informational)" />
    <div class="glass card">
      <DataTable :value="rows" :loading="loading" class="p-datatable-sm">
        <Column field="email" header="User" />
        <Column field="score" header="Score" style="width:5rem" />
        <Column header="Flags">
          <template #body="{ data }">
            <Tag v-for="f in data.flags" :key="f" :value="f" class="mr" severity="warn" />
          </template>
        </Column>
        <Column header="KYC" style="width:5rem">
          <template #body="{ data }">
            <Tag :value="data.is_kyc_verified ? 'yes' : 'no'" :severity="data.is_kyc_verified ? 'success' : 'danger'" />
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 0.5rem; border-radius: 16px; overflow: hidden; }
.mr { margin-right: 0.25rem; margin-bottom: 0.2rem; }
</style>
