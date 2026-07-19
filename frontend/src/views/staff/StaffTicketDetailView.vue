<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { receiptOf, useSupportChat } from '@/composables/useSupportChat'
import type { TicketMessage } from '@/types/api'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()
const auth = useAuthStore()

const ticket = ref<any>(null)
const chatMessages = ref<TicketMessage[]>([])
const body = ref('')
const sending = ref(false)
const messagesEl = ref<HTMLElement | null>(null)

const chat = useSupportChat({
  isStaff: true,
  onMessage: async () => {
    await scrollToBottom()
  },
})

const statusLine = computed(() => {
  if (chat.peerTypingText.value) return chat.peerTypingText.value
  if (chat.presence.value.user_online) return 'Customer is online'
  if (chat.presence.value.user_last_seen) {
    return `Last seen ${shortDate(chat.presence.value.user_last_seen)}`
  }
  return ticket.value?.user_email || ''
})

async function scrollToBottom(force = false) {
  await nextTick()
  const el = messagesEl.value
  if (!el) return
  const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120
  if (force || nearBottom) el.scrollTop = el.scrollHeight
}

async function load() {
  const id = String(route.params.id)
  const { data } = await api.staffTicket(id)
  ticket.value = data
  chatMessages.value = [...(data.messages || [])]
  chat.join(id, chatMessages)
  chat.markRead()
  await scrollToBottom(true)
}

async function reply() {
  if (!body.value.trim() || sending.value) return
  const text = body.value.trim()
  body.value = ''
  chat.sendTyping(false)
  sending.value = true
  const tempId = `tmp-${Date.now()}`
  chatMessages.value.push({
    id: tempId,
    body: text,
    is_staff_reply: true,
    created_at: new Date().toISOString(),
    sender: auth.user?.id || 0,
    sender_name: auth.displayName || 'Staff',
    receipt_status: 'pending',
    _pending: true,
  })
  await scrollToBottom(true)
  try {
    const { data } = await api.staffTicketReply(String(route.params.id), text)
    const msg = data as TicketMessage
    const i = chatMessages.value.findIndex((m) => m.id === tempId)
    if (i >= 0) chatMessages.value[i] = { ...msg, is_staff_reply: true, _pending: false }
    else chat.mergeMessage({ ...msg, is_staff_reply: true })
    if (ticket.value) ticket.value.status = 'waiting'
    await scrollToBottom(true)
  } catch {
    const i = chatMessages.value.findIndex((m) => m.id === tempId)
    if (i >= 0) chatMessages.value[i] = { ...chatMessages.value[i], _pending: false, _failed: true }
    ui.toast('Failed', 'Could not send', 'error')
  } finally {
    sending.value = false
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    reply()
  }
}

function tickTitle(m: TicketMessage) {
  const s = receiptOf(m)
  if (s === 'pending') return 'Sending…'
  if (s === 'read') return 'Read by customer'
  if (s === 'delivered') return 'Delivered'
  return 'Sent'
}

onMounted(load)
onUnmounted(() => chat.leave())
</script>

<template>
  <div>
    <PageHeader :title="ticket?.subject || 'Ticket'" :subtitle="ticket?.user_email">
      <Button label="Back" icon="pi pi-arrow-left" text @click="router.push('/admin/tickets')" />
      <Tag v-if="ticket" :value="ticket.status" :severity="statusSeverity(ticket.status)" />
      <span class="live" :class="{ on: chat.connected }">{{ chat.connected ? 'Live' : 'Sync…' }}</span>
    </PageHeader>

    <div v-if="ticket" class="wa-staff glass">
      <header class="head">
        <div class="avatar" :class="{ online: chat.presence.user_online }">
          {{ (ticket.user_name || ticket.user_email || 'U').slice(0, 1).toUpperCase() }}
        </div>
        <div class="meta">
          <strong>{{ ticket.user_name || ticket.user_email }}</strong>
          <p :class="{ typing: !!chat.peerTypingText }">{{ statusLine }}</p>
        </div>
      </header>

      <div ref="messagesEl" class="messages">
        <div
          v-for="m in chatMessages"
          :key="m.id"
          class="row"
          :class="{ mine: m.is_staff_reply, theirs: !m.is_staff_reply }"
        >
          <div class="bubble">
            <div class="sender">{{ m.is_staff_reply ? 'You (staff)' : m.sender_name }}</div>
            <div class="text">{{ m.body }}</div>
            <div class="foot">
              <span>{{ shortDate(m.created_at) }}</span>
              <span v-if="m.is_staff_reply" class="ticks" :class="receiptOf(m)" :title="tickTitle(m)">
                <template v-if="receiptOf(m) === 'pending'"><i class="pi pi-clock" /></template>
                <template v-else-if="receiptOf(m) === 'sent'"><i class="pi pi-check" /></template>
                <template v-else>
                  <i class="pi pi-check" /><i class="pi pi-check second" />
                </template>
              </span>
            </div>
          </div>
        </div>
        <div v-if="chat.peerTypingText" class="row theirs">
          <div class="bubble typing">
            <span class="dot" /><span class="dot" /><span class="dot" />
          </div>
        </div>
      </div>

      <footer class="composer">
        <textarea
          v-model="body"
          rows="2"
          placeholder="Reply as support…"
          @keydown="onKeydown"
          @input="chat.onComposerInput()"
        />
        <Button icon="pi pi-send" rounded severity="success" :loading="sending" :disabled="!body.trim()" @click="reply" />
      </footer>
    </div>
  </div>
</template>

<style scoped>
.live {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.15);
  color: var(--ci-muted);
}
.live.on { background: rgba(37, 211, 102, 0.15); color: #25D366; }
.wa-staff {
  display: flex;
  flex-direction: column;
  height: min(70vh, 680px);
  border-radius: 18px;
  overflow: hidden;
}
.head {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--ci-border);
  background: rgba(0, 0, 0, 0.15);
}
.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(145deg, #3B82F6, #7C3AED);
  position: relative;
}
.avatar.online::after {
  content: '';
  position: absolute;
  right: 0;
  bottom: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #25D366;
  border: 2px solid var(--ci-bg-elevated, #111827);
}
.meta strong { display: block; }
.meta p {
  margin: 0.1rem 0 0;
  font-size: 0.8rem;
  color: var(--ci-muted);
}
.meta p.typing { color: #25D366; font-weight: 600; }
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  min-height: 0;
}
.row { display: flex; }
.row.mine { justify-content: flex-end; }
.row.theirs { justify-content: flex-start; }
.bubble {
  max-width: min(78%, 520px);
  padding: 0.5rem 0.75rem 0.4rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--ci-border);
}
.row.mine .bubble {
  background: linear-gradient(160deg, #1d4ed8, #1e40af);
  color: #eef2ff;
  border-color: transparent;
}
.sender { font-size: 0.72rem; font-weight: 700; margin-bottom: 0.15rem; opacity: 0.85; }
.text { white-space: pre-wrap; line-height: 1.45; font-size: 0.92rem; }
.foot {
  display: flex;
  justify-content: flex-end;
  gap: 0.3rem;
  align-items: center;
  margin-top: 0.2rem;
  font-size: 0.68rem;
  opacity: 0.8;
}
.ticks {
  display: inline-flex;
  position: relative;
  width: 1.1rem;
  height: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
}
.ticks i { font-size: 0.72rem; position: absolute; left: 0; }
.ticks .second { left: 0.28rem; }
.ticks.read { color: #53bdeb; }
.bubble.typing {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 0.75rem 0.95rem;
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #94a3b8;
  animation: bounce 1.2s ease-in-out infinite;
}
.dot:nth-child(2) { animation-delay: 0.15s; }
.dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
  30% { transform: translateY(-4px); opacity: 1; }
}
.composer {
  display: flex;
  gap: 0.55rem;
  align-items: flex-end;
  padding: 0.75rem;
  border-top: 1px solid var(--ci-border);
  background: rgba(0, 0, 0, 0.12);
}
.composer textarea {
  flex: 1;
  min-height: 48px;
  max-height: 140px;
  resize: none;
  border: 0;
  border-radius: 14px;
  padding: 0.7rem 0.9rem;
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  font: inherit;
  outline: 0;
}
</style>
