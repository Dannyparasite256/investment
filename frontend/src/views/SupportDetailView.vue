<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import Skeleton from 'primevue/skeleton'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'
import { useUiStore } from '@/stores/ui'
import type { SupportTicket } from '@/types/api'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()
const loading = ref(true)
const ticket = ref<SupportTicket | null>(null)
const body = ref('')
const sending = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await api.ticket(String(route.params.id))
    ticket.value = data
  } catch {
    ui.toast('Not found', 'Ticket not found', 'error')
    router.push('/support')
  } finally {
    loading.value = false
  }
}

async function reply() {
  if (!body.value.trim() || !ticket.value) return
  sending.value = true
  try {
    await api.replyTicket(ticket.value.id, body.value.trim())
    body.value = ''
    ui.toast('Sent', 'Reply posted', 'success')
    await load()
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Could not send', 'error')
  } finally {
    sending.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader :title="ticket?.subject || 'Ticket'" :subtitle="ticket ? `Category · ${ticket.category}` : ''">
      <Button label="Back" icon="pi pi-arrow-left" text @click="router.push('/support')" />
      <Tag v-if="ticket" :value="ticket.status" :severity="statusSeverity(ticket.status)" />
    </PageHeader>

    <Skeleton v-if="loading" height="240px" border-radius="18px" />
    <template v-else-if="ticket">
      <div class="thread glass">
        <div
          v-for="m in ticket.messages || []"
          :key="m.id"
          class="msg"
          :class="{ staff: m.is_staff_reply }"
        >
          <div class="meta">
            <strong>{{ m.is_staff_reply ? 'Support' : m.sender_name }}</strong>
            <span class="muted">{{ shortDate(m.created_at) }}</span>
          </div>
          <p>{{ m.body }}</p>
        </div>
      </div>
      <div class="reply glass">
        <Textarea v-model="body" rows="3" class="w-full" placeholder="Write a reply…" />
        <Button label="Send reply" icon="pi pi-send" :loading="sending" class="mt" @click="reply" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.thread { padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1rem; }
.msg {
  padding: 0.85rem 1rem;
  border-radius: 14px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--ci-border);
}
.msg.staff {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.25);
}
.meta { display: flex; justify-content: space-between; gap: 0.5rem; margin-bottom: 0.35rem; font-size: 0.82rem; }
.msg p { margin: 0; white-space: pre-wrap; line-height: 1.5; }
.reply { padding: 1rem; }
.mt { margin-top: 0.75rem; }
</style>
