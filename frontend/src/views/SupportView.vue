<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { api, unwrapList } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { receiptOf, useSupportChat } from '@/composables/useSupportChat'
import { linkify } from '@/utils/linkify'
import { copyText, dayKey, dayLabel, isImageUrl, truncatePreview } from '@/utils/chat'
import type { SupportTicket, TicketMessage, TicketReplyPreview } from '@/types/api'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()
const auth = useAuthStore()

const loading = ref(true)
const tickets = ref<SupportTicket[]>([])
const activeId = ref<string | null>(null)
const activeTicket = ref<SupportTicket | null>(null)
const chatMessages = ref<TicketMessage[]>([])
const loadingChat = ref(false)
const body = ref('')
const sending = ref(false)
const showNew = ref(false)
const saving = ref(false)
const search = ref('')
const messagesEl = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const pendingFile = ref<File | null>(null)
const form = ref({ subject: '', body: '', category: 'general' })
const replyTarget = ref<TicketMessage | null>(null)
const showJump = ref(false)
const lightboxUrl = ref('')
const menuMsgId = ref<string | null>(null)

const chat = useSupportChat({
  isStaff: false,
  onMessage: async () => {
    await scrollToBottom()
  },
})

const categories = [
  { label: 'General', value: 'general' },
  { label: 'Deposit', value: 'deposit' },
  { label: 'Withdrawal', value: 'withdrawal' },
  { label: 'Investment', value: 'investment' },
  { label: 'Account', value: 'account' },
  { label: 'KYC', value: 'kyc' },
  { label: 'Technical', value: 'technical' },
]

type TimelineItem =
  | { kind: 'day'; key: string; label: string }
  | { kind: 'msg'; key: string; msg: TicketMessage }

const timeline = computed<TimelineItem[]>(() => {
  const items: TimelineItem[] = []
  let lastDay = ''
  for (const m of chatMessages.value) {
    const dk = dayKey(m.created_at)
    if (dk && dk !== lastDay) {
      lastDay = dk
      items.push({ kind: 'day', key: `day-${dk}`, label: dayLabel(m.created_at) })
    }
    items.push({ kind: 'msg', key: m.id, msg: m })
  }
  return items
})

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return tickets.value
  return tickets.value.filter(
    (t) =>
      t.subject.toLowerCase().includes(q) ||
      t.category.toLowerCase().includes(q) ||
      t.status.toLowerCase().includes(q),
  )
})

const canReply = computed(() => {
  const s = (activeTicket.value?.status || '').toLowerCase()
  return !!activeTicket.value && !['closed', 'resolved'].includes(s)
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
  if (chat.presence.staff_online) return 'online'
  if (chat.presence.staff_last_seen) {
    return `last seen ${lastSeenLabel(chat.presence.staff_last_seen)}`
  }
  return activeTicket.value ? `${activeTicket.value.category} · support chat` : ''
})

const liveLabel = computed(() => {
  if (chat.connected) return chat.mode === 'ws' ? 'Live' : 'Live · sync'
  return 'Connecting…'
})

function unreadCount(t: SupportTicket): number {
  if (typeof t.unread_count === 'number') return t.unread_count
  const msgs = t.messages || []
  return msgs.filter((m) => m.is_staff_reply && !m.read_at).length
}

function lastPreview(t: SupportTicket): string {
  const msgs = t.messages || []
  if (!msgs.length) return 'No messages yet'
  const last = msgs[msgs.length - 1]
  const who = last.is_staff_reply ? 'Support' : 'You'
  const hasAtt = !!(last.attachment_url || last.attachment)
  let text = (last.body || '').replace(/\s+/g, ' ').trim()
  if (!text || text === '(attachment)') text = hasAtt ? 'Photo' : 'Message'
  const clip = hasAtt ? '📎 ' : ''
  return `${who}: ${clip}${truncatePreview(text, 64)}`
}

function initials(label: string): string {
  const parts = label.trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return 'S'
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
  if (s === 'read') return 'Read'
  if (s === 'delivered') return 'Delivered'
  return 'Sent'
}

function onMessagesScroll() {
  const el = messagesEl.value
  if (!el) return
  const dist = el.scrollHeight - el.scrollTop - el.clientHeight
  showJump.value = dist > 180
}

async function scrollToBottom(force = false) {
  await nextTick()
  const el = messagesEl.value
  if (!el) return
  const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120
  if (force || nearBottom) {
    el.scrollTop = el.scrollHeight
    showJump.value = false
  } else {
    onMessagesScroll()
  }
}

function jumpToLatest() {
  const el = messagesEl.value
  if (!el) return
  el.scrollTop = el.scrollHeight
  showJump.value = false
}

async function loadTickets() {
  loading.value = true
  try {
    const { data } = await api.tickets()
    tickets.value = unwrapList(data)
  } finally {
    loading.value = false
  }
}

async function openTicket(id: string, replace = false) {
  if (!id) return
  activeId.value = id
  replyTarget.value = null
  menuMsgId.value = null
  if (replace) router.replace(`/support/${id}`)
  else if (route.params.id !== id) router.push(`/support/${id}`)

  loadingChat.value = true
  try {
    const { data } = await api.ticket(id)
    activeTicket.value = data
    chatMessages.value = [...(data.messages || [])]
    const idx = tickets.value.findIndex((t) => t.id === id)
    if (idx >= 0) tickets.value[idx] = { ...tickets.value[idx], ...data, unread_count: 0 }
    else tickets.value = [data, ...tickets.value]
    chat.join(id, chatMessages)
    chat.markRead()
    await scrollToBottom(true)
  } catch {
    ui.toast('Not found', 'Conversation not found', 'error')
    activeTicket.value = null
    activeId.value = null
    chat.leave()
    router.replace('/support')
  } finally {
    loadingChat.value = false
  }
}

function closeChat() {
  chat.leave()
  activeId.value = null
  activeTicket.value = null
  chatMessages.value = []
  replyTarget.value = null
  router.push('/support')
}

function onPickFile(e: Event) {
  const input = e.target as HTMLInputElement
  pendingFile.value = input.files?.[0] || null
}

function clearFile() {
  pendingFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

function attachmentHref(m: TicketMessage) {
  return m.attachment_url || m.attachment || m._localPreview || ''
}

function isImageAtt(m: TicketMessage) {
  return isImageUrl(attachmentHref(m))
}

function setReply(m: TicketMessage) {
  replyTarget.value = m
  menuMsgId.value = null
  nextTick(() => {
    const ta = document.querySelector('.wa-composer textarea') as HTMLTextAreaElement | null
    ta?.focus()
  })
}

function clearReply() {
  replyTarget.value = null
}

function quotePreview(m: TicketMessage | TicketReplyPreview | null | undefined): string {
  if (!m) return ''
  const body = (m.body || '').trim()
  if (!body || body === '(attachment)') return '📎 Attachment'
  return truncatePreview(body, 100)
}

function quoteAuthor(m: TicketMessage | TicketReplyPreview): string {
  if ('is_staff_reply' in m && m.is_staff_reply) return 'Support'
  if ('sender_name' in m && m.sender_name) return m.sender_name
  return 'You'
}

async function copyMessage(m: TicketMessage) {
  menuMsgId.value = null
  const text = (m.body || '').trim()
  if (!text || text === '(attachment)') {
    ui.toast('Nothing to copy', 'This message has no text', 'info')
    return
  }
  const ok = await copyText(text)
  ui.toast(ok ? 'Copied' : 'Copy failed', ok ? 'Message copied to clipboard' : 'Could not copy', ok ? 'success' : 'error')
}

function openLightbox(url: string) {
  if (url) lightboxUrl.value = url
}

function closeLightbox() {
  lightboxUrl.value = ''
}

function jumpToQuoted(id?: string | null) {
  if (!id) return
  const el = document.querySelector(`[data-msg-id="${id}"]`) as HTMLElement | null
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  el.classList.add('wa-flash')
  setTimeout(() => el.classList.remove('wa-flash'), 1200)
}

function toggleMenu(id: string) {
  menuMsgId.value = menuMsgId.value === id ? null : id
}

async function reply() {
  if ((!body.value.trim() && !pendingFile.value) || !activeTicket.value || !canReply.value || sending.value) return
  const text = body.value.trim()
  const file = pendingFile.value
  const replyTo = replyTarget.value
  body.value = ''
  clearFile()
  replyTarget.value = null
  chat.sendTyping(false)
  sending.value = true

  const tempId = `tmp-${Date.now()}`
  const optimistic: TicketMessage = {
    id: tempId,
    body: text || (file ? file.name : ''),
    is_staff_reply: false,
    created_at: new Date().toISOString(),
    sender: auth.user?.id || 0,
    sender_name: auth.displayName,
    receipt_status: 'pending',
    _pending: true,
    _localPreview: file && file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
    reply_to_id: replyTo?.id || null,
    reply_to: replyTo
      ? {
          id: replyTo.id,
          body: replyTo.body,
          is_staff_reply: replyTo.is_staff_reply,
          sender_name: replyTo.is_staff_reply ? 'Support' : replyTo.sender_name || 'You',
        }
      : null,
  }
  chatMessages.value.push(optimistic)
  await scrollToBottom(true)

  try {
    const { data } = await api.replyTicket(activeTicket.value.id, text, file, replyTo?.id || null)
    const msg = data as TicketMessage
    const i = chatMessages.value.findIndex((m) => m.id === tempId)
    if (i >= 0) chatMessages.value[i] = { ...msg, _pending: false }
    else chat.mergeMessage(msg)
    activeTicket.value.updated_at = msg.created_at || new Date().toISOString()
    const idx = tickets.value.findIndex((t) => t.id === activeTicket.value!.id)
    if (idx >= 0) {
      tickets.value[idx] = {
        ...tickets.value[idx],
        messages: chatMessages.value,
        updated_at: activeTicket.value.updated_at,
        unread_count: 0,
      }
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

async function create() {
  if (!form.value.subject.trim() || !form.value.body.trim()) {
    ui.toast('Required', 'Subject and message are required', 'warn')
    return
  }
  saving.value = true
  try {
    const { data } = await api.createTicket(form.value)
    ui.toast('Started', 'Conversation opened with support', 'success')
    showNew.value = false
    form.value = { subject: '', body: '', category: 'general' }
    tickets.value = [data, ...tickets.value.filter((t) => t.id !== data.id)]
    await openTicket(data.id, true)
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Could not create ticket', 'error')
  } finally {
    saving.value = false
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    reply()
  }
  if (e.key === 'Escape') {
    if (lightboxUrl.value) closeLightbox()
    else if (replyTarget.value) clearReply()
    else if (menuMsgId.value) menuMsgId.value = null
  }
}

function onInput() {
  if (body.value.trim()) chat.onComposerInput()
  else chat.sendTyping(false)
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
      replyTarget.value = null
    }
  },
)

onMounted(async () => {
  await loadTickets()
  const id = route.params.id
  if (typeof id === 'string' && id) await openTicket(id, true)
})

onUnmounted(() => chat.leave())
</script>

<template>
  <div class="wa-shell" :class="{ 'has-chat': !!activeId }">
    <aside class="wa-sidebar">
      <header class="wa-side-head">
        <div class="wa-side-title">
          <span class="wa-brand-dot" />
          <div>
            <h1>Support</h1>
            <p class="muted">Chat with our team</p>
          </div>
        </div>
        <Button
          icon="pi pi-plus"
          rounded
          severity="success"
          v-tooltip.bottom="'New chat'"
          aria-label="New chat"
          @click="showNew = true"
        />
      </header>

      <div class="wa-search">
        <i class="pi pi-search" />
        <input v-model="search" type="search" placeholder="Search chats" />
      </div>

      <div class="wa-chat-list">
        <div v-if="loading" class="wa-empty-side muted">Loading chats…</div>
        <div v-else-if="!filtered.length" class="wa-empty-side">
          <i class="pi pi-comments" />
          <p>No conversations yet</p>
          <Button label="Start a chat" icon="pi pi-plus" size="small" @click="showNew = true" />
        </div>
        <button
          v-for="t in filtered"
          :key="t.id"
          type="button"
          class="wa-chat-row"
          :class="{ active: activeId === t.id, unread: unreadCount(t) > 0 && activeId !== t.id }"
          @click="openTicket(t.id)"
        >
          <span class="wa-avatar support">{{ initials(t.subject) }}</span>
          <span class="wa-row-body">
            <span class="wa-row-top">
              <strong class="truncate">{{ t.subject }}</strong>
              <span class="wa-time" :class="{ unread: unreadCount(t) > 0 && activeId !== t.id }">
                {{ timeLabel(t.updated_at) }}
              </span>
            </span>
            <span class="wa-row-bot">
              <span class="wa-preview truncate">{{ lastPreview(t) }}</span>
              <span v-if="unreadCount(t) > 0 && activeId !== t.id" class="wa-unread-badge">
                {{ unreadCount(t) > 99 ? '99+' : unreadCount(t) }}
              </span>
              <Tag v-else :value="t.status" :severity="statusSeverity(t.status)" class="wa-status" />
            </span>
          </span>
        </button>
      </div>
    </aside>

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
          <span class="wa-avatar support lg" :class="{ online: chat.presence.staff_online }">S</span>
          <div class="wa-chat-meta">
            <h2 class="truncate">{{ activeTicket.subject }}</h2>
            <p class="status-line" :class="{ typing: !!chat.peerTypingText }">
              <span v-if="chat.presence.staff_online && !chat.peerTypingText" class="dot-online" />
              {{ statusLine }}
            </p>
          </div>
          <span class="live-pill" :class="{ on: chat.connected }">{{ liveLabel }}</span>
        </header>

        <div class="wa-messages-wrap">
          <div
            ref="messagesEl"
            class="wa-messages"
            :class="{ loading: loadingChat }"
            @scroll="onMessagesScroll"
            @click="menuMsgId = null"
          >
            <div class="wa-day-pill muted-start">Conversation started · {{ timeLabel(activeTicket.created_at) }}</div>

            <template v-for="item in timeline" :key="item.key">
              <div v-if="item.kind === 'day'" class="wa-day-pill">{{ item.label }}</div>
              <div
                v-else
                class="wa-bubble-row"
                :class="{ mine: !item.msg.is_staff_reply, theirs: item.msg.is_staff_reply, failed: item.msg._failed }"
                :data-msg-id="item.msg.id"
              >
                <div class="wa-bubble" @contextmenu.prevent="toggleMenu(item.msg.id)">
                  <div v-if="item.msg.is_staff_reply" class="wa-sender">Support</div>

                  <button
                    v-if="item.msg.reply_to"
                    type="button"
                    class="wa-quote"
                    @click.stop="jumpToQuoted(item.msg.reply_to.id)"
                  >
                    <span class="wa-quote-bar" />
                    <span class="wa-quote-body">
                      <span class="wa-quote-author">{{ quoteAuthor(item.msg.reply_to) }}</span>
                      <span class="wa-quote-text">{{ quotePreview(item.msg.reply_to) }}</span>
                    </span>
                  </button>

                  <div
                    v-if="item.msg.body && item.msg.body !== '(attachment)'"
                    class="wa-text"
                    v-html="linkify(item.msg.body)"
                  />

                  <div v-if="attachmentHref(item.msg)" class="wa-attach-wrap">
                    <button
                      v-if="isImageAtt(item.msg)"
                      type="button"
                      class="wa-attach-btn"
                      @click.stop="openLightbox(attachmentHref(item.msg))"
                    >
                      <img :src="attachmentHref(item.msg)" alt="Attachment" class="wa-attach-img" />
                    </button>
                    <a
                      v-else
                      class="wa-attach"
                      :href="attachmentHref(item.msg)"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <span class="wa-attach-file"><i class="pi pi-paperclip" /> Open attachment</span>
                    </a>
                  </div>

                  <div class="wa-meta">
                    <span>{{ msgTime(item.msg.created_at) }}</span>
                    <span
                      v-if="!item.msg.is_staff_reply"
                      class="ticks"
                      :class="receiptOf(item.msg)"
                      :title="tickTitle(item.msg)"
                    >
                      <template v-if="receiptOf(item.msg) === 'pending'">
                        <i class="pi pi-clock" />
                      </template>
                      <template v-else-if="receiptOf(item.msg) === 'sent'">
                        <i class="pi pi-check" />
                      </template>
                      <template v-else>
                        <i class="pi pi-check" /><i class="pi pi-check second" />
                      </template>
                    </span>
                    <span v-if="item.msg._failed" class="fail-hint">Failed</span>
                  </div>

                  <div class="wa-bubble-actions">
                    <button type="button" class="wa-act" title="Reply" @click.stop="setReply(item.msg)">
                      <i class="pi pi-reply" />
                    </button>
                    <button type="button" class="wa-act" title="Copy" @click.stop="copyMessage(item.msg)">
                      <i class="pi pi-copy" />
                    </button>
                  </div>

                  <div v-if="menuMsgId === item.msg.id" class="wa-ctx-menu" @click.stop>
                    <button type="button" @click="setReply(item.msg)"><i class="pi pi-reply" /> Reply</button>
                    <button type="button" @click="copyMessage(item.msg)"><i class="pi pi-copy" /> Copy</button>
                  </div>
                </div>
              </div>
            </template>

            <div v-if="chat.peerTypingText" class="wa-bubble-row theirs typing-row">
              <div class="wa-bubble typing-bubble">
                <span class="dot" /><span class="dot" /><span class="dot" />
              </div>
            </div>

            <div v-if="!chatMessages.length && !loadingChat" class="wa-empty-msgs muted">
              Send a message to start the conversation.
            </div>
          </div>

          <button
            v-if="showJump"
            type="button"
            class="wa-jump"
            title="Jump to latest"
            aria-label="Jump to latest"
            @click="jumpToLatest"
          >
            <i class="pi pi-chevron-down" />
          </button>
        </div>

        <footer v-if="canReply" class="wa-composer-wrap">
          <div v-if="replyTarget" class="wa-reply-chip">
            <span class="wa-reply-bar" />
            <span class="wa-reply-meta">
              <strong>Replying to {{ replyTarget.is_staff_reply ? 'Support' : 'yourself' }}</strong>
              <span class="truncate">{{ quotePreview(replyTarget) }}</span>
            </span>
            <button type="button" class="chip-x" aria-label="Cancel reply" @click="clearReply">×</button>
          </div>
          <div v-if="pendingFile" class="wa-file-chip">
            <i class="pi pi-paperclip" />
            <span class="truncate">{{ pendingFile.name }}</span>
            <button type="button" class="chip-x" @click="clearFile" aria-label="Remove file">×</button>
          </div>
          <div class="wa-composer">
            <input ref="fileInput" type="file" class="hidden-file" accept="image/*,.pdf,.doc,.docx,.txt" @change="onPickFile" />
            <Button icon="pi pi-paperclip" text rounded aria-label="Attach" @click="fileInput?.click()" />
            <textarea
              v-model="body"
              rows="1"
              placeholder="Type a message"
              @keydown="onKeydown"
              @input="onInput"
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
        <footer v-else class="wa-composer closed">
          <span class="muted">This conversation is closed. Open a new chat if you need more help.</span>
          <Button label="New chat" icon="pi pi-plus" size="small" @click="showNew = true" />
        </footer>
      </template>

      <div v-else class="wa-placeholder">
        <div class="wa-placeholder-card">
          <div class="wa-placeholder-icon">
            <i class="pi pi-comments" />
          </div>
          <h2>CryptoInvest Support</h2>
          <p class="muted">
            WhatsApp-style chat with day markers, replies, read receipts, and live typing.
          </p>
          <Button label="New conversation" icon="pi pi-plus" @click="showNew = true" />
          <p v-if="auth.displayName" class="wa-you muted">Signed in as {{ auth.displayName }}</p>
        </div>
      </div>
    </section>

    <Dialog v-model:visible="showNew" modal header="New conversation" class="w-dialog">
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
        <Button label="Start chat" icon="pi pi-send" :loading="saving" @click="create" />
      </div>
    </Dialog>

    <Teleport to="body">
      <div v-if="lightboxUrl" class="wa-lightbox" @click="closeLightbox">
        <button type="button" class="wa-lightbox-x" aria-label="Close" @click="closeLightbox">×</button>
        <img :src="lightboxUrl" alt="Full size" @click.stop />
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
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
.wa-search {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0.55rem 0.75rem;
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
.wa-chat-row.active { background: rgba(37, 211, 102, 0.12); }
.wa-chat-row.unread strong { font-weight: 800; }
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
  gap: 0.2rem;
}
.wa-row-top,
.wa-row-bot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.wa-row-top strong { font-size: 0.95rem; }
.wa-time { font-size: 0.72rem; color: var(--ci-muted); white-space: nowrap; }
.wa-time.unread { color: #25D366; font-weight: 700; }
.wa-preview { font-size: 0.8rem; color: var(--ci-muted); flex: 1; min-width: 0; }
.wa-status { transform: scale(0.85); transform-origin: right center; }
.wa-unread-badge {
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.35rem;
  border-radius: 999px;
  background: #25D366;
  color: #052e16;
  font-size: 0.68rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
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
  background: #0b141a;
}
.wa-chat-head {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.65rem 0.9rem;
  background: rgba(17, 27, 33, 0.95);
  border-bottom: 1px solid var(--ci-border);
  z-index: 2;
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

.wa-messages-wrap {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.wa-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-height: 0;
  background-color: #0b141a;
  background-image:
    radial-gradient(circle at 12% 18%, rgba(37, 211, 102, 0.04) 0, transparent 42%),
    radial-gradient(circle at 88% 72%, rgba(83, 189, 235, 0.04) 0, transparent 38%),
    url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.025'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}
.wa-messages.loading { opacity: 0.65; }
.wa-day-pill {
  align-self: center;
  margin: 0.45rem 0 0.55rem;
  padding: 0.28rem 0.75rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #e9edef;
  background: rgba(17, 27, 33, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  z-index: 1;
}
.wa-day-pill.muted-start {
  color: var(--ci-muted);
  font-weight: 600;
  background: rgba(0, 0, 0, 0.35);
}
.wa-bubble-row { display: flex; width: 100%; }
.wa-bubble-row.mine { justify-content: flex-end; }
.wa-bubble-row.theirs { justify-content: flex-start; }
.wa-bubble-row.wa-flash .wa-bubble {
  animation: waFlash 1.1s ease;
}
@keyframes waFlash {
  0%, 100% { box-shadow: 0 1px 1px rgba(0, 0, 0, 0.18); }
  40% { box-shadow: 0 0 0 3px rgba(37, 211, 102, 0.45); }
}
.wa-bubble {
  max-width: min(78%, 520px);
  padding: 0.45rem 0.65rem 0.35rem;
  border-radius: 10px;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.18);
  word-break: break-word;
  position: relative;
}
.wa-bubble-row.mine .wa-bubble {
  background: linear-gradient(160deg, #005c4b 0%, #025c4c 100%);
  color: #e9fef6;
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
  color: #53bdeb;
  margin-bottom: 0.15rem;
}
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
.wa-bubble-row.mine .wa-text :deep(.chat-link) { color: #a5f3fc; }
.wa-text :deep(.chat-link:hover) { filter: brightness(1.15); }

/* Quote / reply block */
.wa-quote {
  display: flex;
  gap: 0;
  width: 100%;
  margin: 0 0 0.35rem;
  padding: 0;
  border: 0;
  border-radius: 6px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.22);
  cursor: pointer;
  text-align: left;
  color: inherit;
}
.wa-quote:hover { filter: brightness(1.08); }
.wa-quote-bar {
  width: 4px;
  flex-shrink: 0;
  background: #25D366;
}
.wa-bubble-row.theirs .wa-quote-bar { background: #53bdeb; }
.wa-quote-body {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0.3rem 0.5rem;
  min-width: 0;
  flex: 1;
}
.wa-quote-author {
  font-size: 0.72rem;
  font-weight: 700;
  color: #25D366;
}
.wa-bubble-row.theirs .wa-quote-author { color: #53bdeb; }
.wa-quote-text {
  font-size: 0.78rem;
  opacity: 0.85;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  color: rgba(233, 254, 246, 0.65);
}
.ticks i {
  font-size: 0.72rem;
  position: absolute;
  left: 0;
}
.ticks .second { left: 0.28rem; }
.ticks.pending { color: rgba(233, 254, 246, 0.55); }
.ticks.sent { color: rgba(233, 254, 246, 0.7); }
.ticks.delivered { color: rgba(233, 254, 246, 0.85); }
.ticks.read { color: #53bdeb; }
.fail-hint { color: #fca5a5; font-weight: 700; }

.wa-bubble-actions {
  position: absolute;
  top: -0.35rem;
  display: none;
  gap: 0.15rem;
  background: rgba(17, 27, 33, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  padding: 0.1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
  z-index: 3;
}
.wa-bubble-row.mine .wa-bubble-actions { left: -0.25rem; }
.wa-bubble-row.theirs .wa-bubble-actions { right: -0.25rem; }
.wa-bubble:hover .wa-bubble-actions,
.wa-bubble:focus-within .wa-bubble-actions { display: inline-flex; }
.wa-act {
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: #e9edef;
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 0.75rem;
}
.wa-act:hover { background: rgba(255, 255, 255, 0.1); color: #25D366; }

.wa-ctx-menu {
  position: absolute;
  top: 0.4rem;
  right: 0.4rem;
  display: flex;
  flex-direction: column;
  min-width: 120px;
  background: rgba(17, 27, 33, 0.98);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
  z-index: 5;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}
.wa-ctx-menu button {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  border: 0;
  background: transparent;
  color: #e9edef;
  padding: 0.55rem 0.75rem;
  font-size: 0.85rem;
  cursor: pointer;
  text-align: left;
}
.wa-ctx-menu button:hover { background: rgba(37, 211, 102, 0.12); }

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

.wa-jump {
  position: absolute;
  right: 1rem;
  bottom: 0.85rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(17, 27, 33, 0.95);
  color: #e9edef;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
  cursor: pointer;
  display: grid;
  place-items: center;
  z-index: 4;
  transition: transform 0.15s ease, background 0.15s ease;
}
.wa-jump:hover {
  background: #25D366;
  color: #052e16;
  transform: translateY(-2px);
}

.wa-composer-wrap {
  background: rgba(17, 27, 33, 0.96);
  border-top: 1px solid var(--ci-border);
  padding: 0.45rem 0.75rem 0.7rem;
}
.wa-reply-chip {
  display: flex;
  align-items: stretch;
  gap: 0;
  margin-bottom: 0.4rem;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.wa-reply-bar {
  width: 4px;
  background: #25D366;
  flex-shrink: 0;
}
.wa-reply-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0.35rem 0.55rem;
  font-size: 0.78rem;
}
.wa-reply-meta strong { color: #25D366; font-size: 0.72rem; }
.wa-file-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  max-width: 100%;
  margin-bottom: 0.4rem;
  padding: 0.3rem 0.55rem;
  border-radius: 999px;
  background: rgba(37, 211, 102, 0.12);
  font-size: 0.78rem;
}
.chip-x {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0 0.45rem;
}
.hidden-file { display: none; }
.wa-attach-wrap { margin-top: 0.35rem; }
.wa-attach-btn {
  border: 0;
  padding: 0;
  background: transparent;
  cursor: zoom-in;
  display: block;
}
.wa-attach {
  display: block;
  margin-top: 0.4rem;
  text-decoration: none;
  color: #53bdeb;
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
.wa-composer.closed {
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
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
  box-shadow: 0 0 0 2px rgba(37, 211, 102, 0.25);
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
.wa-placeholder-card h2 {
  margin: 0 0 0.5rem;
  font-size: 1.35rem;
  font-weight: 750;
}
.wa-placeholder-card p { margin: 0 0 1rem; line-height: 1.5; }
.wa-you { margin-top: 1.25rem !important; font-size: 0.8rem; }

.form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  min-width: min(420px, 80vw);
}
.form label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--ci-muted);
}

@media (max-width: 900px) {
  .wa-shell {
    grid-template-columns: 1fr;
    height: calc(100dvh - var(--topbar-h, 56px) - var(--bottom-nav-h, 4.25rem) - env(safe-area-inset-bottom, 0px) - 1.25rem);
    height: calc(100svh - var(--topbar-h, 56px) - var(--bottom-nav-h, 4.25rem) - env(safe-area-inset-bottom, 0px) - 1.25rem);
    min-height: 420px;
    max-height: none;
    border-radius: 14px;
    margin: 0;
  }
  .wa-shell.has-chat .wa-sidebar { display: none; }
  .wa-shell:not(.has-chat) .wa-pane { display: none; }
  .wa-back { display: inline-flex; }
  .wa-chat-head {
    padding: 0.55rem 0.65rem;
    gap: 0.45rem;
  }
  .wa-chat-meta h2 { font-size: 0.95rem; }
  .wa-messages { padding: 0.65rem 0.55rem 0.85rem; }
  .wa-bubble { max-width: min(88%, 100%); }
  .wa-bubble-actions { display: inline-flex; opacity: 0.85; }
  .wa-composer-wrap { padding: 0.4rem 0.5rem calc(0.45rem + env(safe-area-inset-bottom, 0px)); }
  .wa-composer textarea {
    min-height: 40px;
    font-size: 16px;
  }
  .wa-side-head { padding: 0.75rem 0.85rem; }
  .wa-placeholder { padding: 1.25rem; }
  .wa-placeholder-card h2 { font-size: 1.15rem; }
}
@media (max-width: 420px) {
  .wa-shell {
    border-radius: 0;
    border-left: 0;
    border-right: 0;
  }
}
</style>

<style>
/* Lightbox must be global (Teleport to body) */
.wa-lightbox {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.92);
  display: grid;
  place-items: center;
  padding: 1.5rem;
  cursor: zoom-out;
}
.wa-lightbox img {
  max-width: min(96vw, 1100px);
  max-height: 90vh;
  border-radius: 10px;
  object-fit: contain;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  cursor: default;
}
.wa-lightbox-x {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 40px;
  height: 40px;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  font-size: 1.5rem;
  cursor: pointer;
  line-height: 1;
}
</style>
