<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import InputText from 'primevue/inputtext'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { formatMoney, shortDate } from '@/utils/money'

const rows = ref<any[]>([])
const loading = ref(true)
const q = ref('')

async function load() {
  loading.value = true
  try {
    const { data } = await api.staffUsers({ q: q.value || undefined })
    rows.value = data.results || []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Admin · Users" subtitle="Accounts overview">
      <InputText v-model="q" placeholder="Search email / name" @keyup.enter="load" />
      <Button icon="pi pi-search" @click="load" />
      <Button as="a" href="/staff/users/" label="Full staff users" text />
    </PageHeader>
    <div class="glass card">
      <DataTable :value="rows" :loading="loading" paginator :rows="15" class="p-datatable-sm">
        <Column field="email" header="Email" />
        <Column field="name" header="Name" />
        <Column header="Balance">
          <template #body="{ data }"><span class="mono">{{ formatMoney(data.available) }}</span></template>
        </Column>
        <Column field="preferred_currency" header="Currency" style="width:6rem" />
        <Column header="Flags">
          <template #body="{ data }">
            <Tag v-if="data.is_kyc_verified" value="KYC" severity="success" class="me" />
            <Tag v-if="!data.is_active" value="Off" severity="danger" />
            <Tag :value="data.role" severity="info" />
          </template>
        </Column>
        <Column header="Joined">
          <template #body="{ data }">{{ shortDate(data.date_joined) }}</template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 0.5rem; }
.me { margin-right: 0.25rem; }
</style>
