<script setup lang="ts">
/**
 * Admin support — same WhatsApp-style chat shell as the customer Support page.
 */
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { api } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { receiptOf, useSupportChat } from '@/composables/useSupportChat'
import { linkify } from '@/utils/linkify'
import type { TicketMessage } from '@/types/api'

interface StaffTicketRow {
  id: string
  subject: string
  status: string
  priority?: string
  category?: string
  user_email: string
  user_name?: string
  created_at?: string
  updated_at: string
  message_count?: number
  last_message?: {
    id: string
    body: string
    is_staff_reply: boolean
    created_at: string
    receipt_status?: string
  } | null
  messages?: TicketMessage[]
}

const route = useRoute()
const router = useRouter()
const ui = useUiStore()
const auth = useAuthStore()

const loading = ref(true)
const tickets = ref<StaffTicketRow[]>([])
const activeId = ref<string | null>(null)
const activeTicket = ref<StaffTicketRow | null>(null)
const chatMessages = ref<TicketMessage[]>([])
const loadingChat = ref(false)
const body = ref('')
const sending = ref(false)
const search = ref('')
const statusFilter = ref('')
const messagesEl = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const pendingFile = ref<File | null>(null)
const canned = ref<{ id: string; title: string; body: string; category: string }[]>([])
const cannedId = ref<string | null>(null)

const statusOptions = [
  { label: 'All statuses', value: '' },
  { label: 'Open', value: 'open' },
  { label: 'In progress', value: 'in_progress' },
  { label: 'Waiting', value: 'waiting' },
  { label: 'Resolved', value: 'resolved' },
  { label: 'Closed', value: 'closed' },
]

const chat = useSupportChat({
  isStaff: true,
  onMessage: async () => {
    await scrollToBottom()
    await loadTickets(false)
  },
})

const filtered = computed(() => {
  let list = tickets.value
  if (statusFilter.value) {
    list = list.filter((t) => t.status === statusFilter.value)
  }
  const q = search.value.trim().toLowerCase()
  if (!q) return list
  return list.filter(
    (t) =>
      t.subject.toLowerCase().includes(q) ||
      (t.user_email || '').toLowerCase().includes(q) ||
      (t.user_name || '').toLowerCase().includes(q) ||
      (t.category || '').toLowerCase().includes(q),
  )
})

function lastSeenLabel(iso?: string | null): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    const secs = Math.floor((Date.now() - d.getTime()) / 1000)
    if (secs < 45) return 'just now'
    if (secs < 3600) return `${Math.max(1, Math.floor(secs / 60))} min ago`
    if (secs < 86400) {
      const h = Math.floor(secs / 3600)
      return `${h} hour${h === 1 ? '' : 's'} ago`
    }
    return timeLabel(iso)
  } catch {
    return timeLabel(iso)
  }
}

const statusLine = computed(() => {
  if (chat.peerTypingText) return chat.peerTypingText
  if (chat.presence.user_online) return 'online'
  if (chat.presence.user_last_seen) {
    return `last seen ${lastSeenLabel(chat.presence.user_last_seen)}`
  }
  return activeTicket.value
    ? `${activeTicket.value.user_email} · ${activeTicket.value.category || 'support'}`
    : ''
})

const liveLabel = computed(() => {
  if (chat.connected) return chat.mode === 'ws' ? 'Live' : 'Live · sync'
  return 'Connecting…'
})

function lastPreview(t: StaffTicketRow): string {
  const last = t.last_message
  if (!last) {
    const msgs = t.messages || []
    if (!msgs.length) return 'No messages yet'
    const m = msgs[msgs.length - 1]
    const who = m.is_staff_reply ? 'You' : 'Customer'
    const text = (m.body || '').replace(/\s+/g, ' ').trim()
    return `${who}: ${text.slice(0, 72)}${text.length > 72 ? '…' : ''}`
  }
  const who = last.is_staff_reply ? 'You' : 'Customer'
  const text = (last.body || '').replace(/\s+/g, ' ').trim()
  return `${who}: ${text.slice(0, 72)}${text.length > 72 ? '…' : ''}`
}

function initials(t: StaffTicketRow): string {
  const label = t.user_name || t.user_email || t.subject || 'U'
  const parts = label.trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return 'U'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
}

function timeLabel(iso?: string | null): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    const now = new Date()
    const sameDay =
      d.getFullYear() === now.getFullYear() &&
      d.getMonth() === now.getMonth() &&
      d.getDate() === now.getDate()
    if (sameDay) {
      return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
    }
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  } catch {
    return shortDate(iso)
  }
}

function msgTime(iso?: string): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

function tickTitle(m: TicketMessage): string {
  const s = receiptOf(m)
  if (s === 'pending') return 'Sending…'
  if (s === 'read') return 'Read by customer'
  if (s === 'delivered') return 'Delivered'
  return 'Sent'
}

async function scrollToBottom(force = false) {
  await nextTick()
  const el = messagesEl.value
  if (!el) return
  const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120
  if (force || nearBottom) el.scrollTop = el.scrollHeight
}

async function loadTickets(showLoader = true) {
  if (showLoader) loading.value = true
  try {
    const { data } = await api.staffTickets()
    tickets.value = data.results || []
  } finally {
    loading.value = false
  }
}

async function openTicket(id: string, replace = false) {
  if (!id) return
  activeId.value = id
  if (replace) router.replace(`/admin/tickets/${id}`)
  else if (route.params.id !== id) router.push(`/admin/tickets/${id}`)

  loadingChat.value = true
  try {
    const { data } = await api.staffTicket(id)
    activeTicket.value = {
      id: data.id,
      subject: data.subject,
      status: data.status,
      category: data.category,
      priority: data.priority,
      user_email: data.user_email,
      user_name: data.user_name,
      created_at: data.created_at,
      updated_at: data.updated_at,
      messages: data.messages,
    }
    chatMessages.value = [...(data.messages || [])]
    const idx = tickets.value.findIndex((t) => t.id === id)
    if (idx >= 0) {
      tickets.value[idx] = {
        ...tickets.value[idx],
        ...activeTicket.value,
        last_message: chatMessages.value.length
          ? {
              id: chatMessages.value[chatMessages.value.length - 1].id,
              body: chatMessages.value[chatMessages.value.length - 1].body,
              is_staff_reply: chatMessages.value[chatMessages.value.length - 1].is_staff_reply,
              created_at: chatMessages.value[chatMessages.value.length - 1].created_at,
              receipt_status: chatMessages.value[chatMessages.value.length - 1].receipt_status,
            }
          : null,
      }
    }
    chat.join(id, chatMessages)
    chat.markRead()
    await scrollToBottom(true)
  } catch {
    ui.toast('Not found', 'Ticket not found', 'error')
    activeTicket.value = null
    activeId.value = null
    chat.leave()
    router.replace('/admin/tickets')
  } finally {
    loadingChat.value = false
  }
}

function closeChat() {
  chat.leave()
  activeId.value = null
  activeTicket.value = null
  chatMessages.value = []
  router.push('/admin/tickets')
}

function onPickFile(e: Event) {
  const input = e.target as HTMLInputElement
  pendingFile.value = input.files?.[0] || null
}
function clearFile() {
  pendingFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}
function applyCanned() {
  const row = canned.value.find((c) => c.id === cannedId.value)
  if (row) body.value = row.body
}
function attachmentHref(m: TicketMessage) {
  return m.attachment_url || m.attachment || m._localPreview || ''
}
function isImageAtt(m: TicketMessage) {
  const u = attachmentHref(m).toLowerCase()
  return /\.(png|jpe?g|gif|webp|bmp)(\?|$)/i.test(u) || (m._localPreview || '').startsWith('blob:')
}

async function reply() {
  if ((!body.value.trim() && !pendingFile.value) || !activeTicket.value || sending.value) return
  const text = body.value.trim()
  const file = pendingFile.value
  body.value = ''
  clearFile()
  chat.sendTyping(false)
  sending.value = true

  const tempId = `tmp-${Date.now()}`
  const optimistic: TicketMessage = {
    id: tempId,
    body: text || (file ? file.name : ''),
    is_staff_reply: true,
    created_at: new Date().toISOString(),
    sender: auth.user?.id || 0,
    sender_name: auth.displayName || 'Staff',
    receipt_status: 'pending',
    _pending: true,
    _localPreview: file && file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
  }
  chatMessages.value.push(optimistic)
  await scrollToBottom(true)

  try {
    const { data } = await api.staffTicketReply(activeTicket.value.id, text, file)
    const msg = { ...(data as TicketMessage), is_staff_reply: true }
    const i = chatMessages.value.findIndex((m) => m.id === tempId)
    if (i >= 0) chatMessages.value[i] = { ...msg, _pending: false }
    else chat.mergeMessage(msg)
    activeTicket.value.status = 'waiting'
    activeTicket.value.updated_at = msg.created_at || new Date().toISOString()
    const idx = tickets.value.findIndex((t) => t.id === activeTicket.value!.id)
    if (idx >= 0) {
      tickets.value[idx] = {
        ...tickets.value[idx],
        status: 'waiting',
        updated_at: activeTicket.value.updated_at,
        last_message: {
          id: msg.id,
          body: msg.body,
          is_staff_reply: true,
          created_at: msg.created_at,
          receipt_status: msg.receipt_status,
        },
      }
      // Move to top
      const [row] = tickets.value.splice(idx, 1)
      tickets.value.unshift(row)
    }
    await scrollToBottom(true)
  } catch (e: any) {
    const i = chatMessages.value.findIndex((m) => m.id === tempId)
    if (i >= 0) {
      chatMessages.value[i] = { ...chatMessages.value[i], _pending: false, _failed: true }
    }
    ui.toast('Failed', e?.response?.data?.detail || 'Could not send', 'error')
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

watch(
  () => route.params.id,
  (id) => {
    if (typeof id === 'string' && id) {
      if (activeId.value !== id) openTicket(id, true)
    } else {
      chat.leave()
      activeId.value = null
      activeTicket.value = null
      chatMessages.value = []
    }
  },
)

onMounted(async () => {
  await loadTickets()
  try {
    const { data } = await api.staffCannedReplies()
    canned.value = (data as any).results || []
  } catch { /* optional */ }
  const id = route.params.id
  if (typeof id === 'string' && id) await openTicket(id, true)
})

onUnmounted(() => chat.leave())
</script>

<template>
  <div class="wa-shell staff" :class="{ 'has-chat': !!activeId }">
    <!-- Sidebar: same layout as customer -->
    <aside class="wa-sidebar">
      <header class="wa-side-head">
        <div class="wa-side-title">
          <span class="wa-brand-dot staff" />
          <div>
            <h1>Support</h1>
            <p class="muted">Admin inbox · same chat UI</p>
          </div>
        </div>
        <Button
          icon="pi pi-refresh"
          rounded
          text
          v-tooltip.bottom="'Refresh'"
          aria-label="Refresh"
          @click="loadTickets()"
        />
      </header>

      <div class="wa-filters">
        <div class="wa-search">
          <i class="pi pi-search" />
          <input v-model="search" type="search" placeholder="Search customer or subject" />
        </div>
        <Select
          v-model="statusFilter"
          :options="statusOptions"
          option-label="label"
          option-value="value"
          class="status-filter"
          placeholder="Status"
        />
      </div>

      <div class="wa-chat-list">
        <div v-if="loading" class="wa-empty-side muted">Loading chats…</div>
        <div v-else-if="!filtered.length" class="wa-empty-side">
          <i class="pi pi-comments" />
          <p>No support chats</p>
        </div>
        <button
          v-for="t in filtered"
          :key="t.id"
          type="button"
          class="wa-chat-row"
          :class="{ active: activeId === t.id }"
          @click="openTicket(t.id)"
        >
          <span class="wa-avatar customer">{{ initials(t) }}</span>
          <span class="wa-row-body">
            <span class="wa-row-top">
              <strong class="truncate">{{ t.user_name || t.user_email }}</strong>
              <span class="wa-time">{{ timeLabel(t.updated_at) }}</span>
            </span>
            <span class="wa-row-sub truncate muted">{{ t.subject }}</span>
            <span class="wa-row-bot">
              <span class="wa-preview truncate">{{ lastPreview(t) }}</span>
              <Tag :value="t.status" :severity="statusSeverity(t.status)" class="wa-status" />
            </span>
          </span>
        </button>
      </div>
    </aside>

    <!-- Chat pane — identical bubble / ticks / typing UX -->
    <section class="wa-pane">
      <template v-if="activeTicket">
        <header class="wa-chat-head">
          <Button
            icon="pi pi-arrow-left"
            text
            rounded
            class="wa-back"
            aria-label="Back"
            @click="closeChat"
          />
          <span class="wa-avatar customer lg" :class="{ online: chat.presence.user_online }">
            {{ initials(activeTicket) }}
          </span>
          <div class="wa-chat-meta">
            <h2 class="truncate">{{ activeTicket.user_name || activeTicket.user_email }}</h2>
            <p class="status-line" :class="{ typing: !!chat.peerTypingText }">
              <span v-if="chat.presence.user_online && !chat.peerTypingText" class="dot-online" />
              {{ statusLine }}
            </p>
            <p class="subject-line truncate muted">{{ activeTicket.subject }}</p>
          </div>
          <Tag :value="activeTicket.status" :severity="statusSeverity(activeTicket.status)" />
          <span class="live-pill" :class="{ on: chat.connected }">{{ liveLabel }}</span>
        </header>

        <div ref="messagesEl" class="wa-messages" :class="{ loading: loadingChat }">
          <div class="wa-day-pill">
            Conversation · {{ timeLabel(activeTicket.created_at) }}
          </div>
          <div
            v-for="m in chatMessages"
            :key="m.id"
            class="wa-bubble-row"
            :class="{ mine: m.is_staff_reply, theirs: !m.is_staff_reply, failed: m._failed }"
          >
            <div class="wa-bubble">
              <div class="wa-sender">
                {{ m.is_staff_reply ? 'You (support)' : (m.sender_name || 'Customer') }}
              </div>
              <div v-if="m.body" class="wa-text" v-html="linkify(m.body)" />
              <a
                v-if="attachmentHref(m)"
                class="wa-attach"
                :href="attachmentHref(m)"
                target="_blank"
                rel="noopener noreferrer"
              >
                <img v-if="isImageAtt(m)" :src="attachmentHref(m)" alt="Attachment" class="wa-attach-img" />
                <span v-else class="wa-attach-file"><i class="pi pi-paperclip" /> Open attachment</span>
              </a>
              <div class="wa-meta">
                <span>{{ msgTime(m.created_at) }}</span>
                <span
                  v-if="m.is_staff_reply"
                  class="ticks"
                  :class="receiptOf(m)"
                  :title="tickTitle(m)"
                >
                  <template v-if="receiptOf(m) === 'pending'">
                    <i class="pi pi-clock" />
                  </template>
                  <template v-else-if="receiptOf(m) === 'sent'">
                    <i class="pi pi-check" />
                  </template>
                  <template v-else>
                    <i class="pi pi-check" /><i class="pi pi-check second" />
                  </template>
                </span>
                <span v-if="m._failed" class="fail-hint">Failed</span>
              </div>
            </div>
          </div>

          <div v-if="chat.peerTypingText" class="wa-bubble-row theirs typing-row">
            <div class="wa-bubble typing-bubble">
              <span class="dot" /><span class="dot" /><span class="dot" />
            </div>
          </div>

          <div v-if="!chatMessages.length && !loadingChat" class="wa-empty-msgs muted">
            No messages yet. Send the first reply.
          </div>
        </div>

        <footer class="wa-composer-wrap">
          <div v-if="canned.length" class="wa-canned">
            <Select
              v-model="cannedId"
              :options="canned"
              option-label="title"
              option-value="id"
              placeholder="Canned reply…"
              class="canned-select"
              show-clear
              @update:model-value="applyCanned"
            />
          </div>
          <div v-if="pendingFile" class="wa-file-chip">
            <i class="pi pi-paperclip" />
            <span class="truncate">{{ pendingFile.name }}</span>
            <button type="button" class="chip-x" @click="clearFile" aria-label="Remove file">×</button>
          </div>
          <div class="wa-composer">
            <input
              ref="fileInput"
              type="file"
              class="hidden-file"
              accept="image/*,.pdf,.doc,.docx,.txt"
              @change="onPickFile"
            />
            <Button icon="pi pi-paperclip" text rounded aria-label="Attach" @click="fileInput?.click()" />
            <textarea
              v-model="body"
              rows="1"
              placeholder="Type a reply as support…"
              @keydown="onKeydown"
              @input="body.trim() ? chat.onComposerInput() : chat.sendTyping(false)"
            />
            <Button
              icon="pi pi-send"
              rounded
              severity="success"
              :loading="sending"
              :disabled="!body.trim() && !pendingFile"
              aria-label="Send"
              @click="reply"
            />
          </div>
        </footer>
      </template>

      <div v-else class="wa-placeholder">
        <div class="wa-placeholder-card">
          <div class="wa-placeholder-icon staff">
            <i class="pi pi-headphones" />
          </div>
          <h2>Support inbox</h2>
          <p class="muted">
            Same chat experience as customers: live messages, typing indicators, and read receipts.
            Select a conversation on the left to reply.
          </p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* Shared WhatsApp shell — matches customer SupportView */
.wa-shell {
  display: grid;
  grid-template-columns: minmax(280px, 360px) 1fr;
  height: calc(100dvh - 7.5rem);
  min-height: 520px;
  max-height: 900px;
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid var(--ci-border);
  background: var(--ci-bg-elevated, rgba(15, 23, 42, 0.55));
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
}
.wa-sidebar {
  display: flex;
  flex-direction: column;
  min-width: 0;
  border-right: 1px solid var(--ci-border);
  background: rgba(0, 0, 0, 0.18);
}
.wa-side-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  background: rgba(17, 27, 33, 0.92);
  border-bottom: 1px solid var(--ci-border);
}
.wa-side-title {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-width: 0;
}
.wa-side-title h1 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.wa-side-title p { margin: 0; font-size: 0.75rem; }
.wa-brand-dot {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  flex-shrink: 0;
  background: linear-gradient(145deg, #25D366, #128C7E);
  box-shadow: 0 0 0 3px rgba(37, 211, 102, 0.2);
}
.wa-brand-dot.staff {
  background: linear-gradient(145deg, #3B82F6, #7C3AED);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
}
.wa-filters {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0 0.75rem 0.55rem;
}
.wa-search {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.75rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--ci-border);
}
.wa-search i { color: var(--ci-muted); font-size: 0.85rem; }
.wa-search input {
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  color: inherit;
  font-size: 0.88rem;
}
.status-filter { width: 100%; }
:deep(.status-filter .p-select) {
  width: 100%;
  border-radius: 10px;
  font-size: 0.85rem;
}
.wa-chat-list { flex: 1; overflow-y: auto; min-height: 0; }
.wa-empty-side {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  padding: 2.5rem 1rem;
  text-align: center;
  color: var(--ci-muted);
}
.wa-empty-side i { font-size: 1.8rem; opacity: 0.6; }
.wa-chat-row {
  width: 100%;
  display: flex;
  gap: 0.75rem;
  align-items: center;
  padding: 0.75rem 0.9rem;
  border: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
}
.wa-chat-row:hover { background: rgba(255, 255, 255, 0.05); }
.wa-chat-row.active { background: rgba(59, 130, 246, 0.14); }
.wa-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  font-weight: 800;
  font-size: 0.85rem;
  color: #fff;
  background: linear-gradient(145deg, #128C7E, #075E54);
  position: relative;
}
.wa-avatar.customer {
  background: linear-gradient(145deg, #3B82F6, #7C3AED);
}
.wa-avatar.lg { width: 42px; height: 42px; }
.wa-avatar.online::after {
  content: '';
  position: absolute;
  right: 1px;
  bottom: 1px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #25D366;
  border: 2px solid rgba(17, 27, 33, 0.95);
}
.wa-row-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.12rem;
}
.wa-row-top,
.wa-row-bot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.wa-row-top strong { font-size: 0.95rem; }
.wa-row-sub { font-size: 0.78rem; }
.wa-time { font-size: 0.72rem; color: var(--ci-muted); white-space: nowrap; }
.wa-preview { font-size: 0.8rem; color: var(--ci-muted); flex: 1; min-width: 0; }
.wa-status { transform: scale(0.85); transform-origin: right center; }
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wa-pane {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  background:
    linear-gradient(180deg, rgba(11, 20, 26, 0.55), rgba(11, 20, 26, 0.75)),
    radial-gradient(circle at 20% 10%, rgba(59, 130, 246, 0.06), transparent 40%);
}
.wa-chat-head {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.65rem 0.9rem;
  background: rgba(17, 27, 33, 0.95);
  border-bottom: 1px solid var(--ci-border);
}
.wa-chat-meta { min-width: 0; flex: 1; }
.wa-chat-meta h2 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}
.status-line {
  margin: 0.1rem 0 0;
  font-size: 0.78rem;
  color: var(--ci-muted);
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.status-line.typing { color: #25D366; font-weight: 600; }
.subject-line { margin: 0.1rem 0 0; font-size: 0.72rem; }
.dot-online {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #25D366;
  box-shadow: 0 0 0 3px rgba(37, 211, 102, 0.2);
}
.live-pill {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.15);
  color: var(--ci-muted);
  white-space: nowrap;
}
.live-pill.on {
  background: rgba(37, 211, 102, 0.15);
  color: #25D366;
}
.wa-back { display: none; }

.wa-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-height: 0;
}
.wa-messages.loading { opacity: 0.65; }
.wa-day-pill {
  align-self: center;
  margin: 0.35rem 0 0.75rem;
  padding: 0.28rem 0.7rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--ci-muted);
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.wa-bubble-row { display: flex; width: 100%; }
.wa-bubble-row.mine { justify-content: flex-end; }
.wa-bubble-row.theirs { justify-content: flex-start; }
.wa-bubble {
  max-width: min(78%, 520px);
  padding: 0.45rem 0.65rem 0.35rem;
  border-radius: 10px;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.18);
  word-break: break-word;
}
/* Staff (mine) uses blue; customer (theirs) uses dark — mirrors inverted customer view */
.wa-bubble-row.mine .wa-bubble {
  background: linear-gradient(160deg, #1d4ed8 0%, #1e40af 100%);
  color: #eef2ff;
  border-top-right-radius: 3px;
}
.wa-bubble-row.theirs .wa-bubble {
  background: rgba(32, 44, 51, 0.95);
  color: #e9edef;
  border-top-left-radius: 3px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}
.wa-bubble-row.failed .wa-bubble {
  outline: 1px solid rgba(248, 113, 113, 0.5);
}
.wa-sender {
  font-size: 0.72rem;
  font-weight: 700;
  color: #93c5fd;
  margin-bottom: 0.15rem;
}
.wa-bubble-row.theirs .wa-sender { color: #53bdeb; }
.wa-text {
  font-size: 0.92rem;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
}
.wa-text :deep(.chat-link) {
  color: #53bdeb;
  text-decoration: underline;
  text-underline-offset: 2px;
  font-weight: 600;
  word-break: break-all;
}
.wa-bubble-row.mine .wa-text :deep(.chat-link) {
  color: #bfdbfe;
}
.wa-text :deep(.chat-link:hover) {
  filter: brightness(1.15);
}
.wa-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.28rem;
  margin-top: 0.2rem;
  font-size: 0.68rem;
  opacity: 0.85;
}
.ticks {
  display: inline-flex;
  align-items: center;
  position: relative;
  width: 1.1rem;
  height: 0.85rem;
  color: rgba(238, 242, 255, 0.7);
}
.ticks i {
  font-size: 0.72rem;
  position: absolute;
  left: 0;
}
.ticks .second { left: 0.28rem; }
.ticks.pending { color: rgba(238, 242, 255, 0.55); }
.ticks.sent { color: rgba(238, 242, 255, 0.7); }
.ticks.delivered { color: rgba(238, 242, 255, 0.85); }
.ticks.read { color: #53bdeb; }
.fail-hint { color: #fca5a5; font-weight: 700; }

.typing-bubble {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 0.7rem 0.9rem !important;
  min-width: 52px;
}
.typing-bubble .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #94a3b8;
  animation: bounce 1.2s ease-in-out infinite;
}
.typing-bubble .dot:nth-child(2) { animation-delay: 0.15s; }
.typing-bubble .dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
  30% { transform: translateY(-4px); opacity: 1; }
}

.wa-empty-msgs { text-align: center; margin: auto; padding: 2rem; }

.wa-composer-wrap {
  background: rgba(17, 27, 33, 0.96);
  border-top: 1px solid var(--ci-border);
  padding: 0.45rem 0.75rem 0.7rem;
}
.wa-canned {
  margin-bottom: 0.4rem;
}
.canned-select {
  width: 100%;
  max-width: 280px;
}
.wa-file-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  max-width: 100%;
  margin-bottom: 0.4rem;
  padding: 0.3rem 0.55rem;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.15);
  font-size: 0.78rem;
}
.chip-x {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
}
.hidden-file { display: none; }
.wa-attach {
  display: block;
  margin-top: 0.4rem;
  text-decoration: none;
  color: #93c5fd;
  font-size: 0.85rem;
  font-weight: 600;
}
.wa-attach-img {
  max-width: min(220px, 70vw);
  max-height: 180px;
  border-radius: 8px;
  display: block;
  object-fit: cover;
}
.wa-attach-file { display: inline-flex; align-items: center; gap: 0.35rem; }
.wa-composer {
  display: flex;
  align-items: flex-end;
  gap: 0.35rem;
}
.wa-composer textarea {
  flex: 1;
  min-height: 42px;
  max-height: 120px;
  resize: none;
  border: 0;
  border-radius: 22px;
  padding: 0.7rem 1rem;
  background: rgba(255, 255, 255, 0.08);
  color: inherit;
  outline: 0;
  font: inherit;
  line-height: 1.35;
}
.wa-composer textarea:focus {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.35);
}

.wa-placeholder {
  flex: 1;
  display: grid;
  place-items: center;
  padding: 2rem;
}
.wa-placeholder-card { max-width: 380px; text-align: center; }
.wa-placeholder-icon {
  width: 88px;
  height: 88px;
  margin: 0 auto 1rem;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(37, 211, 102, 0.12);
  border: 1px solid rgba(37, 211, 102, 0.25);
  color: #25D366;
  font-size: 2rem;
}
.wa-placeholder-icon.staff {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.3);
  color: #60A5FA;
}
.wa-placeholder-card h2 {
  margin: 0 0 0.5rem;
  font-size: 1.35rem;
  font-weight: 750;
}
.wa-placeholder-card p { margin: 0 0 1rem; line-height: 1.5; }

@media (max-width: 900px) {
  .wa-shell {
    grid-template-columns: 1fr;
    height: calc(100dvh - var(--topbar-h, 56px) - var(--bottom-nav-h, 4.25rem) - env(safe-area-inset-bottom, 0px) - 1.25rem);
    height: calc(100svh - var(--topbar-h, 56px) - var(--bottom-nav-h, 4.25rem) - env(safe-area-inset-bottom, 0px) - 1.25rem);
    min-height: 420px;
    max-height: none;
    border-radius: 14px;
  }
  .wa-shell.has-chat .wa-sidebar { display: none; }
  .wa-shell:not(.has-chat) .wa-pane { display: none; }
  .wa-back { display: inline-flex; }
  .wa-chat-head { padding: 0.55rem 0.65rem; gap: 0.45rem; }
  .wa-messages { padding: 0.65rem 0.55rem 0.85rem; }
  .wa-bubble { max-width: min(88%, 100%); }
  .wa-composer-wrap { padding: 0.4rem 0.5rem calc(0.45rem + env(safe-area-inset-bottom, 0px)); }
  .wa-composer textarea { min-height: 40px; font-size: 16px; }
  .wa-filters { padding: 0 0.65rem 0.5rem; }
}
</style>
