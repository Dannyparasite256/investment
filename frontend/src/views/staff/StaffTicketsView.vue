<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'

const router = useRouter()
const rows = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.staffTickets()
    rows.value = data.results || []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="Admin · Support tickets" subtitle="Reply to user tickets" />
    <div class="glass card">
      <DataTable
        :value="rows"
        :loading="loading"
        row-hover
        class="p-datatable-sm"
        @row-click="(e: any) => router.push(`/admin/tickets/${e.data.id}`)"
      >
        <Column field="subject" header="Subject" />
        <Column field="user_email" header="User" />
        <Column header="Status">
          <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity(data.status)" /></template>
        </Column>
        <Column header="Updated">
          <template #body="{ data }">{{ shortDate(data.updated_at) }}</template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 0.5rem; }
:deep(.p-datatable-tbody > tr) { cursor: pointer; }
</style>
