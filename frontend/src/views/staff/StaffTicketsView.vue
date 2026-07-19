<script setup lang="ts">
/**
 * Admin support — same WhatsApp-style chat shell as the customer Support page.
 */
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { api } from '@/services/api'
import { shortDate, statusSeverity } from '@/utils/money'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { receiptOf, useSupportChat } from '@/composables/useSupportChat'
import { linkify } from '@/utils/linkify'
import { copyText, dayKey, dayLabel, isImageUrl, truncatePreview } from '@/utils/chat'
import { createVoiceRecorder, isVoiceUrl } from '@/utils/voiceNote'
import type { TicketMessage, TicketReplyPreview } from '@/types/api'

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
  unread_count?: number
  last_message?: {
    id: string
    body: string
    is_staff_reply: boolean
    created_at: string
    receipt_status?: string
    delivered_at?: string | null
    read_at?: string | null
    has_attachment?: boolean
  } | null
  muted?: boolean
  pinned?: boolean
  sla_due_at?: string | null
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
const replyTarget = ref<TicketMessage | null>(null)
const showJump = ref(false)
const lightboxUrl = ref('')
const menuMsgId = ref<string | null>(null)
const recording = ref(false)
const recordSecs = ref(0)
const voiceBusy = ref(false)
const forwardMsg = ref<TicketMessage | null>(null)
const forwardTargetId = ref<string | null>(null)
const forwardBusy = ref(false)
const mentionHits = ref<{ id: number; handle: string; name: string; email: string }[]>([])
const showMentions = ref(false)
let voiceRec = createVoiceRecorder()
let recordTimer: ReturnType<typeof setInterval> | null = null
let mentionTimer: ReturnType<typeof setTimeout> | null = null

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
  sound: true,
  onMessage: async () => {
    await scrollToBottom()
    await loadTickets(false)
  },
})

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

function unreadCount(t: StaffTicketRow): number {
  return typeof t.unread_count === 'number' ? t.unread_count : 0
}

function lastPreview(t: StaffTicketRow): string {
  const last = t.last_message
  if (!last) {
    const msgs = t.messages || []
    if (!msgs.length) return 'No messages yet'
    const m = msgs[msgs.length - 1]
    const who = m.is_staff_reply ? 'You' : 'Customer'
    const hasAtt = !!(m.attachment_url || m.attachment)
    let text = (m.body || '').replace(/\s+/g, ' ').trim()
    if (!text || text === '(attachment)') text = hasAtt ? 'Photo' : 'Message'
    return `${who}: ${hasAtt ? '📎 ' : ''}${truncatePreview(text, 64)}`
  }
  const who = last.is_staff_reply ? 'You' : 'Customer'
  const hasAtt = !!last.has_attachment
  let text = (last.body || '').replace(/\s+/g, ' ').trim()
  if (!text || text === '(attachment)') text = hasAtt ? 'Photo' : 'Message'
  return `${who}: ${hasAtt ? '📎 ' : ''}${truncatePreview(text, 64)}`
}

function lastReceipt(t: StaffTicketRow): string {
  const last = t.last_message
  if (!last || !last.is_staff_reply) return ''
  if (last.read_at || last.receipt_status === 'read') return 'read'
  if (last.delivered_at || last.receipt_status === 'delivered') return 'delivered'
  return 'sent'
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

function onMessagesScroll() {
  const el = messagesEl.value
  if (!el) return
  showJump.value = el.scrollHeight - el.scrollTop - el.clientHeight > 180
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
  replyTarget.value = null
  menuMsgId.value = null
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
      unread_count: 0,
    }
    chatMessages.value = [...(data.messages || [])]
    const idx = tickets.value.findIndex((t) => t.id === id)
    if (idx >= 0) {
      tickets.value[idx] = {
        ...tickets.value[idx],
        ...activeTicket.value,
        unread_count: 0,
        last_message: chatMessages.value.length
          ? {
              id: chatMessages.value[chatMessages.value.length - 1].id,
              body: chatMessages.value[chatMessages.value.length - 1].body,
              is_staff_reply: chatMessages.value[chatMessages.value.length - 1].is_staff_reply,
              created_at: chatMessages.value[chatMessages.value.length - 1].created_at,
              receipt_status: chatMessages.value[chatMessages.value.length - 1].receipt_status,
              has_attachment: !!(
                chatMessages.value[chatMessages.value.length - 1].attachment_url ||
                chatMessages.value[chatMessages.value.length - 1].attachment
              ),
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
  replyTarget.value = null
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
  return isImageUrl(attachmentHref(m))
}
function isVoiceAtt(m: TicketMessage) {
  return !!m.is_voice || isVoiceUrl(attachmentHref(m), m.is_voice)
}

async function toggleRecord() {
  if (!activeTicket.value) return
  if (recording.value) {
    try {
      voiceBusy.value = true
      const { blob } = await voiceRec.stop()
      recording.value = false
      if (recordTimer) { clearInterval(recordTimer); recordTimer = null }
      if (blob.size < 200) {
        ui.toast('Too short', 'Hold longer for a voice note', 'warn')
        return
      }
      const { data } = await api.staffReplyVoice(activeTicket.value.id, blob)
      const msg = { ...(data as TicketMessage), is_staff_reply: true, is_voice: true }
      chatMessages.value.push(msg)
      await scrollToBottom(true)
      await loadTickets(false)
    } catch (e: any) {
      ui.toast('Voice failed', e?.response?.data?.detail || e?.message || 'Could not send', 'error')
      try { voiceRec.cancel() } catch { /* */ }
      recording.value = false
    } finally {
      voiceBusy.value = false
      recordSecs.value = 0
      voiceRec = createVoiceRecorder()
    }
    return
  }
  try {
    await voiceRec.start()
    recording.value = true
    recordSecs.value = 0
    recordTimer = setInterval(() => { recordSecs.value += 1 }, 1000)
  } catch {
    ui.toast('Mic blocked', 'Allow microphone access', 'error')
  }
}

async function doForward() {
  if (!activeTicket.value || !forwardMsg.value || !forwardTargetId.value) return
  forwardBusy.value = true
  try {
    await api.staffTicketForward(activeTicket.value.id, forwardMsg.value.id, forwardTargetId.value)
    ui.toast('Forwarded', 'Message copied to the other ticket', 'success')
    forwardMsg.value = null
    forwardTargetId.value = null
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Could not forward', 'error')
  } finally {
    forwardBusy.value = false
  }
}

const forwardOptions = computed(() =>
  tickets.value
    .filter((t) => t.id !== activeId.value)
    .map((t) => ({
      label: `${t.user_name || t.user_email} · ${t.subject}`,
      value: t.id,
    })),
)

function onBodyInput() {
  if (body.value.trim()) chat.onComposerInput()
  else chat.sendTyping(false)
  // @mention autocomplete
  const m = body.value.match(/(?:^|\s)@([A-Za-z0-9._+-]{0,40})$/)
  if (!m) {
    showMentions.value = false
    return
  }
  const q = m[1]
  if (mentionTimer) clearTimeout(mentionTimer)
  mentionTimer = setTimeout(async () => {
    try {
      const { data } = await api.staffDirectory(q)
      mentionHits.value = data.results || []
      showMentions.value = mentionHits.value.length > 0
    } catch {
      showMentions.value = false
    }
  }, 180)
}

function pickMention(h: { handle: string }) {
  body.value = body.value.replace(/(?:^|\s)@([A-Za-z0-9._+-]{0,40})$/, (all) => {
    const lead = all.startsWith(' ') || all.startsWith('\n') ? all[0] : ''
    return `${lead}@${h.handle} `
  })
  showMentions.value = false
}

function richBody(m: TicketMessage): string {
  const html = linkify(m.body || '')
  return html.replace(/@([A-Za-z0-9._+-]{2,40})/g, '<span class="wa-mention">@$1</span>')
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
  if (m.is_staff_reply) return 'You (support)'
  return m.sender_name || 'Customer'
}
async function copyMessage(m: TicketMessage) {
  menuMsgId.value = null
  const text = (m.body || '').trim()
  if (!text || text === '(attachment)') {
    ui.toast('Nothing to copy', 'This message has no text', 'info')
    return
  }
  const ok = await copyText(text)
  ui.toast(ok ? 'Copied' : 'Copy failed', ok ? 'Message copied' : 'Could not copy', ok ? 'success' : 'error')
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
  if ((!body.value.trim() && !pendingFile.value) || !activeTicket.value || sending.value) return
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
    is_staff_reply: true,
    created_at: new Date().toISOString(),
    sender: auth.user?.id || 0,
    sender_name: auth.displayName || 'Staff',
    receipt_status: 'pending',
    _pending: true,
    _localPreview: file && file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
    reply_to_id: replyTo?.id || null,
    reply_to: replyTo
      ? {
          id: replyTo.id,
          body: replyTo.body,
          is_staff_reply: replyTo.is_staff_reply,
          sender_name: replyTo.is_staff_reply ? 'Support' : replyTo.sender_name || 'Customer',
        }
      : null,
  }
  chatMessages.value.push(optimistic)
  await scrollToBottom(true)

  try {
    const { data } = await api.staffTicketReply(activeTicket.value.id, text, file, replyTo?.id || null)
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
        unread_count: 0,
        last_message: {
          id: msg.id,
          body: msg.body,
          is_staff_reply: true,
          created_at: msg.created_at,
          receipt_status: msg.receipt_status,
          has_attachment: !!(msg.attachment_url || msg.attachment),
        },
      }
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
  if (e.key === 'Escape') {
    if (lightboxUrl.value) closeLightbox()
    else if (replyTarget.value) clearReply()
    else if (menuMsgId.value) menuMsgId.value = null
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
      replyTarget.value = null
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
          :class="{ active: activeId === t.id, unread: unreadCount(t) > 0 && activeId !== t.id }"
          @click="openTicket(t.id)"
        >
          <span class="wa-avatar customer">{{ initials(t) }}</span>
          <span class="wa-row-body">
            <span class="wa-row-top">
              <strong class="truncate">{{ t.user_name || t.user_email }}</strong>
              <span class="wa-time" :class="{ unread: unreadCount(t) > 0 && activeId !== t.id }">
                {{ timeLabel(t.updated_at) }}
              </span>
            </span>
            <span class="wa-row-sub truncate muted">{{ t.subject }}</span>
            <span class="wa-row-bot">
              <span class="wa-preview truncate">
                <span
                  v-if="lastReceipt(t)"
                  class="ticks list-ticks"
                  :class="lastReceipt(t)"
                >
                  <template v-if="lastReceipt(t) === 'sent'"><i class="pi pi-check" /></template>
                  <template v-else>
                    <i class="pi pi-check" /><i class="pi pi-check second" />
                  </template>
                </span>
                {{ lastPreview(t) }}
              </span>
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

        <div class="wa-messages-wrap">
          <div
            ref="messagesEl"
            class="wa-messages"
            :class="{ loading: loadingChat }"
            @scroll="onMessagesScroll"
            @click="menuMsgId = null"
          >
            <div class="wa-day-pill muted-start">Conversation · {{ timeLabel(activeTicket.created_at) }}</div>

            <template v-for="item in timeline" :key="item.key">
              <div v-if="item.kind === 'day'" class="wa-day-pill">{{ item.label }}</div>
              <div
                v-else
                class="wa-bubble-row"
                :class="{ mine: item.msg.is_staff_reply, theirs: !item.msg.is_staff_reply, failed: item.msg._failed }"
                :data-msg-id="item.msg.id"
              >
                <div class="wa-bubble" @contextmenu.prevent="toggleMenu(item.msg.id)">
                  <div class="wa-sender">
                    {{ item.msg.is_staff_reply ? 'You (support)' : (item.msg.sender_name || 'Customer') }}
                  </div>

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

                  <div v-if="item.msg.is_forwarded" class="wa-fwd-label">↪️ Forwarded</div>
                  <div
                    v-if="item.msg.body && item.msg.body !== '(attachment)' && !item.msg.is_deleted"
                    class="wa-text"
                    v-html="richBody(item.msg)"
                  />
                  <div v-else-if="item.msg.is_deleted" class="wa-text deleted">🚫 This message was deleted</div>

                  <div v-if="attachmentHref(item.msg) && !item.msg.is_deleted" class="wa-attach-wrap">
                    <button
                      v-if="isImageAtt(item.msg)"
                      type="button"
                      class="wa-attach-btn"
                      @click.stop="openLightbox(attachmentHref(item.msg))"
                    >
                      <img :src="attachmentHref(item.msg)" alt="Attachment" class="wa-attach-img" />
                    </button>
                    <div v-else-if="isVoiceAtt(item.msg)" class="wa-voice">
                      <i class="pi pi-microphone" />
                      <audio controls preload="metadata" :src="attachmentHref(item.msg)" />
                    </div>
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
                      v-if="item.msg.is_staff_reply"
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
                    <button type="button" class="wa-act" title="Forward" @click.stop="forwardMsg = item.msg">
                      <i class="pi pi-share-alt" />
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
              No messages yet. Send the first reply.
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
          <div v-if="replyTarget" class="wa-reply-chip">
            <span class="wa-reply-bar" />
            <span class="wa-reply-meta">
              <strong>Replying to {{ replyTarget.is_staff_reply ? 'yourself' : (replyTarget.sender_name || 'customer') }}</strong>
              <span class="truncate">{{ quotePreview(replyTarget) }}</span>
            </span>
            <button type="button" class="chip-x" aria-label="Cancel reply" @click="clearReply">×</button>
          </div>
          <div v-if="pendingFile" class="wa-file-chip">
            <i class="pi pi-paperclip" />
            <span class="truncate">{{ pendingFile.name }}</span>
            <button type="button" class="chip-x" @click="clearFile" aria-label="Remove file">×</button>
          </div>
          <div class="wa-composer-rel">
            <div v-if="showMentions" class="wa-mention-menu">
              <button
                v-for="h in mentionHits"
                :key="h.id"
                type="button"
                @click="pickMention(h)"
              >
                <strong>@{{ h.handle }}</strong>
                <span class="muted">{{ h.name }}</span>
              </button>
            </div>
            <div class="wa-composer">
              <input
                ref="fileInput"
                type="file"
                class="hidden-file"
                accept="image/*,audio/*,.pdf,.doc,.docx,.txt"
                @change="onPickFile"
              />
              <Button icon="pi pi-paperclip" text rounded aria-label="Attach" @click="fileInput?.click()" />
              <Button
                :icon="recording ? 'pi pi-stop' : 'pi pi-microphone'"
                text
                rounded
                :severity="recording ? 'danger' : 'secondary'"
                :loading="voiceBusy"
                @click="toggleRecord"
              />
              <textarea
                v-model="body"
                rows="1"
                :placeholder="recording ? `Recording… ${recordSecs}s` : 'Type a reply… use @name to mention staff'"
                :disabled="recording"
                @keydown="onKeydown"
                @input="onBodyInput"
              />
              <Button
                icon="pi pi-send"
                rounded
                severity="success"
                :loading="sending"
                :disabled="recording || (!body.trim() && !pendingFile)"
                aria-label="Send"
                @click="reply"
              />
            </div>
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
            WhatsApp-style admin chat: day markers, reply quotes, unread badges, and live typing.
          </p>
        </div>
      </div>
    </section>

    <Dialog
      :visible="!!forwardMsg"
      modal
      header="Forward to ticket"
      @update:visible="(v: boolean) => { if (!v) forwardMsg = null }"
    >
      <div class="form" style="min-width:min(360px,80vw);display:flex;flex-direction:column;gap:.75rem">
        <Select
          v-model="forwardTargetId"
          :options="forwardOptions"
          option-label="label"
          option-value="value"
          placeholder="Choose ticket"
          class="w-full"
        />
        <Button label="Forward" icon="pi pi-share-alt" :loading="forwardBusy" :disabled="!forwardTargetId" @click="doForward" />
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
.wa-avatar.customer { background: linear-gradient(145deg, #3B82F6, #7C3AED); }
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
  box-shadow: 0 0 0 2px rgba(37, 211, 102, 0.15);
}
.list-ticks {
  display: inline-flex !important;
  position: relative;
  width: 1rem;
  height: 0.75rem;
  vertical-align: middle;
  margin-right: 0.15rem;
  color: #94a3b8;
}
.list-ticks i { font-size: 0.65rem; position: absolute; left: 0; }
.list-ticks .second { left: 0.25rem; }
.list-ticks.read { color: #53bdeb !important; }
.list-ticks.delivered { color: #94a3b8 !important; }
.wa-voice {
  display: flex; align-items: center; gap: 0.45rem; margin-top: 0.35rem;
  padding: 0.35rem 0.5rem; border-radius: 10px; background: rgba(0,0,0,0.18);
}
.wa-voice audio { max-width: min(240px, 60vw); height: 32px; }
.wa-fwd-label { font-size: 0.7rem; font-weight: 700; opacity: 0.75; margin-bottom: 0.2rem; }
.wa-composer-rel { position: relative; }
.wa-mention-menu {
  position: absolute; left: 0; right: 0; bottom: 100%;
  margin-bottom: 0.35rem; max-height: 180px; overflow: auto;
  background: rgba(17,27,33,0.98); border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px; z-index: 20; box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.wa-mention-menu button {
  width: 100%; display: flex; gap: 0.5rem; border: 0; background: transparent;
  color: inherit; padding: 0.5rem 0.75rem; text-align: left; cursor: pointer; font-size: 0.85rem;
}
.wa-mention-menu button:hover { background: rgba(59,130,246,0.15); }
.wa-text :deep(.wa-mention) { color: #93c5fd; font-weight: 700; }
.wa-text.deleted { opacity: 0.7; font-style: italic; }
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
    radial-gradient(circle at 12% 18%, rgba(59, 130, 246, 0.05) 0, transparent 42%),
    radial-gradient(circle at 88% 72%, rgba(124, 58, 237, 0.04) 0, transparent 38%),
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
  color: #e9edef;
  background: rgba(17, 27, 33, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
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
  40% { box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.5); }
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
.wa-bubble-row.mine .wa-text :deep(.chat-link) { color: #bfdbfe; }
.wa-text :deep(.chat-link:hover) { filter: brightness(1.15); }

.wa-quote {
  display: flex;
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
  background: #93c5fd;
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
  color: #93c5fd;
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
.wa-act:hover { background: rgba(255, 255, 255, 0.1); color: #93c5fd; }

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
.wa-ctx-menu button:hover { background: rgba(59, 130, 246, 0.15); }

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
}
.wa-jump:hover {
  background: #3B82F6;
  color: #fff;
}

.wa-composer-wrap {
  background: rgba(17, 27, 33, 0.96);
  border-top: 1px solid var(--ci-border);
  padding: 0.45rem 0.75rem 0.7rem;
}
.wa-canned { margin-bottom: 0.4rem; }
.canned-select { width: 100%; max-width: 280px; }
.wa-reply-chip {
  display: flex;
  align-items: stretch;
  margin-bottom: 0.4rem;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.wa-reply-bar { width: 4px; background: #3B82F6; flex-shrink: 0; }
.wa-reply-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0.35rem 0.55rem;
  font-size: 0.78rem;
}
.wa-reply-meta strong { color: #93c5fd; font-size: 0.72rem; }
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
  .wa-bubble-actions { display: inline-flex; opacity: 0.85; }
  .wa-composer-wrap { padding: 0.4rem 0.5rem calc(0.45rem + env(safe-area-inset-bottom, 0px)); }
  .wa-composer textarea { min-height: 40px; font-size: 16px; }
  .wa-filters { padding: 0 0.65rem 0.5rem; }
}
</style>
