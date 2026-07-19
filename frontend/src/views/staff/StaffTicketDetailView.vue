<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()
const ticket = ref<any>(null)
const body = ref('')
const sending = ref(false)

async function load() {
  const { data } = await api.staffTicket(String(route.params.id))
  ticket.value = data
}

async function reply() {
  if (!body.value.trim()) return
  sending.value = true
  try {
    await api.staffTicketReply(String(route.params.id), body.value.trim())
    body.value = ''
    ui.toast('Sent', 'Staff reply posted', 'success')
    await load()
  } catch {
    ui.toast('Failed', 'Could not send', 'error')
  } finally {
    sending.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader :title="ticket?.subject || 'Ticket'" :subtitle="ticket?.user_email">
      <Button label="Back" icon="pi pi-arrow-left" text @click="router.push('/admin/tickets')" />
      <Tag v-if="ticket" :value="ticket.status" :severity="statusSeverity(ticket.status)" />
    </PageHeader>
    <div v-if="ticket" class="thread glass">
      <div v-for="m in ticket.messages" :key="m.id" class="msg" :class="{ staff: m.is_staff_reply }">
        <div class="meta">
          <strong>{{ m.is_staff_reply ? 'Staff' : m.sender_name }}</strong>
          <span class="muted">{{ shortDate(m.created_at) }}</span>
        </div>
        <p>{{ m.body }}</p>
      </div>
    </div>
    <div class="glass reply">
      <Textarea v-model="body" rows="3" class="w-full" placeholder="Staff reply…" />
      <Button label="Send reply" icon="pi pi-send" class="mt" :loading="sending" @click="reply" />
    </div>
  </div>
</template>

<style scoped>
.thread { padding: 1rem; display: flex; flex-direction: column; gap: 0.65rem; margin-bottom: 1rem; }
.msg { padding: 0.85rem; border-radius: 12px; border: 1px solid var(--ci-border); background: rgba(255,255,255,0.03); }
.msg.staff { background: rgba(59,130,246,0.1); }
.meta { display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.3rem; }
.msg p { margin: 0; white-space: pre-wrap; }
.reply { padding: 1rem; }
.mt { margin-top: 0.65rem; }
</style>
