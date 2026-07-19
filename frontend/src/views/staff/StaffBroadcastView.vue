<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const title = ref('')
const message = ref('')
const vip = ref('')
const sending = ref(false)

async function send() {
  if (!title.value.trim() || !message.value.trim()) return
  sending.value = true
  try {
    const { data } = await api.staffBroadcast({
      title: title.value.trim(),
      message: message.value.trim(),
      vip_slug: vip.value.trim() || undefined,
    })
    ui.toast('Sent', `Notified ${data.sent_count} users`, 'success')
    title.value = ''
    message.value = ''
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Broadcast failed', 'error')
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader title="Bulk notify" subtitle="Push an announcement to all users or a VIP tier" />
    <div class="glass form">
      <label>Title <InputText v-model="title" class="w-full" /></label>
      <label>Message <Textarea v-model="message" rows="5" class="w-full" /></label>
      <label>VIP slug filter (optional) <InputText v-model="vip" class="w-full" placeholder="gold" /></label>
      <Button label="Send broadcast" icon="pi pi-megaphone" :loading="sending" @click="send" />
    </div>
  </div>
</template>

<style scoped>
.form { display: grid; gap: 0.85rem; padding: 1.1rem; border-radius: 16px; max-width: 520px; }
.form label { display: grid; gap: 0.35rem; font-size: 0.85rem; font-weight: 600; color: var(--ci-muted); }
</style>
