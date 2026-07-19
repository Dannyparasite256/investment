<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api, unwrapList } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import type { KYCDocument } from '@/types/api'

const auth = useAuthStore()
const ui = useUiStore()
const docs = ref<KYCDocument[]>([])
const loading = ref(true)
const saving = ref(false)
const form = ref({
  document_type: 'passport',
  document_number: '',
  front: null as File | null,
  back: null as File | null,
  selfie: null as File | null,
})
const types = [
  { label: 'Passport', value: 'passport' },
  { label: 'National ID', value: 'national_id' },
  { label: 'Driver license', value: 'drivers_license' },
]

function onFile(e: Event, key: 'front' | 'back' | 'selfie') {
  const input = e.target as HTMLInputElement
  form.value[key] = input.files?.[0] || null
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.kycList()
    docs.value = unwrapList(data as any)
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!form.value.document_number || !form.value.front) {
    ui.toast('Required', 'Document number and front image are required', 'warn')
    return
  }
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('document_type', form.value.document_type)
    fd.append('document_number', form.value.document_number)
    if (form.value.front) fd.append('front_image', form.value.front)
    if (form.value.back) fd.append('back_image', form.value.back)
    if (form.value.selfie) fd.append('selfie_image', form.value.selfie)
    await api.submitKyc(fd)
    ui.toast('Submitted', 'KYC documents are under review', 'success')
    await load()
    await auth.fetchMe()
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Upload failed', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Identity verification (KYC)" subtitle="Verify your account to unlock higher limits">
      <Tag
        :value="auth.user?.is_kyc_verified ? 'Verified' : 'Not verified'"
        :severity="auth.user?.is_kyc_verified ? 'success' : 'warn'"
      />
    </PageHeader>

    <div class="grid">
      <div class="glass card">
        <h3>Submit documents</h3>
        <div class="form">
          <label>Document type
            <Select v-model="form.document_type" :options="types" option-label="label" option-value="value" class="w-full" />
          </label>
          <label>Document number
            <InputText v-model="form.document_number" class="w-full" />
          </label>
          <label>Front image *
            <input type="file" accept="image/*" @change="onFile($event, 'front')" />
          </label>
          <label>Back image
            <input type="file" accept="image/*" @change="onFile($event, 'back')" />
          </label>
          <label>Selfie
            <input type="file" accept="image/*" @change="onFile($event, 'selfie')" />
          </label>
          <Button label="Submit KYC" icon="pi pi-upload" :loading="saving" @click="submit" />
        </div>
      </div>

      <div class="glass card">
        <h3>Submissions</h3>
        <p v-if="!docs.length" class="muted">No KYC submissions yet.</p>
        <ul v-else class="list">
          <li v-for="d in docs" :key="d.id">
            <div>
              <strong>{{ d.document_type }}</strong>
              <div class="muted small">{{ d.document_number }} · {{ shortDate(d.created_at) }}</div>
              <div v-if="d.rejection_reason" class="danger small">{{ d.rejection_reason }}</div>
            </div>
            <Tag :value="d.status" :severity="statusSeverity(d.status)" />
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
.card { padding: 1.15rem; }
.form { display: flex; flex-direction: column; gap: 0.75rem; margin-top: 0.75rem; }
.form label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.85rem; font-weight: 600; color: var(--ci-muted); }
.list { list-style: none; padding: 0; margin: 0.75rem 0 0; display: flex; flex-direction: column; gap: 0.65rem; }
.list li { display: flex; justify-content: space-between; gap: 0.75rem; padding: 0.75rem; border-radius: 12px; border: 1px solid var(--ci-border); }
.small { font-size: 0.8rem; }
.danger { color: var(--ci-danger); }
</style>
