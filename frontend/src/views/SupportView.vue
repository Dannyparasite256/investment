<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api, unwrapList } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'
import { useUiStore } from '@/stores/ui'
import type { SupportTicket } from '@/types/api'

const router = useRouter()
const ui = useUiStore()
const loading = ref(true)
const tickets = ref<SupportTicket[]>([])
const showNew = ref(false)
const saving = ref(false)
const form = ref({ subject: '', body: '', category: 'general' })
const categories = [
  { label: 'General', value: 'general' },
  { label: 'Deposit', value: 'deposit' },
  { label: 'Withdrawal', value: 'withdrawal' },
  { label: 'Investment', value: 'investment' },
  { label: 'Account', value: 'account' },
  { label: 'KYC', value: 'kyc' },
]

async function load() {
  loading.value = true
  try {
    const { data } = await api.tickets()
    tickets.value = unwrapList(data)
  } finally {
    loading.value = false
  }
}

async function create() {
  if (!form.value.subject.trim() || !form.value.body.trim()) {
    ui.toast('Required', 'Subject and message are required', 'warn')
    return
  }
  saving.value = true
  try {
    const { data } = await api.createTicket(form.value)
    ui.toast('Ticket created', 'Our team will reply soon', 'success')
    showNew.value = false
    form.value = { subject: '', body: '', category: 'general' }
    router.push(`/support/${data.id}`)
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Could not create ticket', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Support" subtitle="Tickets and help from our team">
      <Button label="New ticket" icon="pi pi-plus" @click="showNew = true" />
    </PageHeader>

    <div class="glass card">
      <EmptyState v-if="!loading && !tickets.length" title="No tickets yet" text="Open a ticket if you need help with deposits, KYC, or investments." />
      <DataTable v-else :value="tickets" :loading="loading" row-hover class="p-datatable-sm" @row-click="(e: any) => router.push(`/support/${e.data.id}`)">
        <Column field="subject" header="Subject" />
        <Column field="category" header="Category" style="width:7rem" />
        <Column header="Status" style="width:8rem">
          <template #body="{ data }">
            <Tag :value="data.status" :severity="statusSeverity(data.status)" />
          </template>
        </Column>
        <Column header="Updated" style="width:9rem">
          <template #body="{ data }">{{ shortDate(data.updated_at) }}</template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="showNew" modal header="New support ticket" class="w-dialog">
      <div class="form">
        <label>Category
          <Select v-model="form.category" :options="categories" option-label="label" option-value="value" class="w-full" />
        </label>
        <label>Subject
          <InputText v-model="form.subject" class="w-full" placeholder="Brief summary" />
        </label>
        <label>Message
          <Textarea v-model="form.body" rows="5" class="w-full" placeholder="Describe your issue…" />
        </label>
        <Button label="Submit ticket" icon="pi pi-send" :loading="saving" @click="create" />
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
.card { padding: 0.5rem; overflow: hidden; border-radius: 18px; }
.form { display: flex; flex-direction: column; gap: 0.85rem; min-width: min(420px, 80vw); }
.form label { display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.85rem; font-weight: 600; color: var(--ci-muted); }
:deep(.p-datatable-tbody > tr) { cursor: pointer; }
</style>
