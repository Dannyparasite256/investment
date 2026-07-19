/**
 * Realtime support chat: HTTP poll is always the source of truth
 * (works on PythonAnywhere). WebSocket is optional bonus.
 */
import { onUnmounted, reactive, ref, type Ref } from 'vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type {
  ChatPresence,
  ChatTyper,
  ReceiptStatus,
  TicketMessage,
} from '@/types/api'

/** How long peer typing may show without a fresh event (ms). */
const PEER_TYPING_MAX_MS = 3500

export function receiptOf(m: TicketMessage): ReceiptStatus {
  if (m._pending) return 'pending'
  if (m._failed) return 'sent'
  if (m.read_at || m.receipt_status === 'read') return 'read'
  if (m.delivered_at || m.receipt_status === 'delivered') return 'delivered'
  return 'sent'
}

function wsUrl(token: string | null): string {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host = window.location.host
  const q = token ? `?token=${encodeURIComponent(token)}` : ''
  return `${proto}://${host}/ws/support/${q}`
}

function sameUser(a: unknown, b: unknown): boolean {
  if (a == null || b == null) return false
  return String(a) === String(b)
}

export function useSupportChat(options: {
  isStaff?: boolean
  onMessage?: (m: TicketMessage) => void
}) {
  const auth = useAuthStore()
  const connected = ref(false)
  const mode = ref<'ws' | 'poll' | 'idle'>('idle')
  const typing = ref<ChatTyper[]>([])
  const presence = ref<ChatPresence>({})
  const peerTypingText = ref('')

  let ws: WebSocket | null = null
  let pollTimer: ReturnType<typeof setInterval> | null = null
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  let typingTimer: ReturnType<typeof setTimeout> | null = null
  let typingPulse: ReturnType<typeof setInterval> | null = null
  let peerTypingExpiry: ReturnType<typeof setTimeout> | null = null
  let lastTypingSent = false
  let activeTicketId: string | null = null
  let sinceIso: string | null = null
  let destroyed = false
  let messagesRef: Ref<TicketMessage[]> | null = null
  let pollInFlight = false
  /** Last time we received a positive peer-typing signal (ws or poll). */
  let peerTypingSeenAt = 0

  function setMessagesRef(r: Ref<TicketMessage[]>) {
    messagesRef = r
  }

  function mergeMessage(m: TicketMessage) {
    if (!messagesRef || !m?.id) return
    const list = messagesRef.value
    const idx = list.findIndex((x) => String(x.id) === String(m.id))
    if (idx >= 0) {
      list[idx] = { ...list[idx], ...m, _pending: false, _failed: false }
    } else {
      const pendingIdx = list.findIndex(
        (x) => x._pending && x.body === m.body && !!x.is_staff_reply === !!m.is_staff_reply,
      )
      if (pendingIdx >= 0) list.splice(pendingIdx, 1)
      list.push(m)
      list.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      options.onMessage?.(m)
    }
    if (m.created_at && (!sinceIso || m.created_at > sinceIso)) {
      sinceIso = m.created_at
    }
  }

  function applyReceipts(receipts: TicketMessage[]) {
    if (!messagesRef || !receipts?.length) return
    const map = new Map(receipts.map((r) => [String(r.id), r]))
    messagesRef.value = messagesRef.value.map((m) => {
      const r = map.get(String(m.id))
      if (!r) return m
      return {
        ...m,
        delivered_at: r.delivered_at ?? m.delivered_at,
        read_at: r.read_at ?? m.read_at,
        receipt_status: r.receipt_status ?? m.receipt_status,
      }
    })
  }

  function applyReceiptIds(ids: string[], status: string, at?: string) {
    if (!messagesRef || !ids?.length) return
    const set = new Set(ids.map(String))
    messagesRef.value = messagesRef.value.map((m) => {
      if (!set.has(String(m.id))) return m
      if (status === 'read') {
        return {
          ...m,
          read_at: at || m.read_at || new Date().toISOString(),
          delivered_at: m.delivered_at || at || new Date().toISOString(),
          receipt_status: 'read',
        }
      }
      if (status === 'delivered') {
        return {
          ...m,
          delivered_at: at || m.delivered_at || new Date().toISOString(),
          receipt_status: m.read_at ? 'read' : 'delivered',
        }
      }
      return m
    })
  }

  /** Keep only the peer side (customer never sees own typing; staff never sees own). */
  function filterPeerTypers(list: ChatTyper[] | null | undefined): ChatTyper[] {
    if (!list?.length) return []
    const me = auth.user?.id
    return list.filter((t) => {
      if (!t) return false
      if (sameUser(t.user_id, me)) return false
      // Customer UI: only staff typers
      if (!options.isStaff && !t.is_staff) return false
      // Staff UI: only customer typers
      if (options.isStaff && t.is_staff) return false
      return true
    })
  }

  function clearPeerTyping() {
    typing.value = []
    peerTypingText.value = ''
    peerTypingSeenAt = 0
    if (peerTypingExpiry) {
      clearTimeout(peerTypingExpiry)
      peerTypingExpiry = null
    }
  }

  function schedulePeerTypingExpiry() {
    if (peerTypingExpiry) clearTimeout(peerTypingExpiry)
    peerTypingExpiry = setTimeout(() => {
      // Auto-hide if no fresh signal (missed typing:false or stale poll)
      if (Date.now() - peerTypingSeenAt >= PEER_TYPING_MAX_MS - 50) {
        clearPeerTyping()
      }
    }, PEER_TYPING_MAX_MS)
  }

  function updateTyping(list: ChatTyper[] | null | undefined) {
    const peers = filterPeerTypers(list)
    if (!peers.length) {
      clearPeerTyping()
      return
    }
    typing.value = peers
    peerTypingSeenAt = Date.now()
    const names = peers.map((t) => (t.is_staff ? 'Support' : t.name || 'Customer'))
    peerTypingText.value =
      names.length === 1 ? `${names[0]} is typing…` : `${names.join(', ')} are typing…`
    schedulePeerTypingExpiry()
  }

  function handleEvent(data: any) {
    if (!data || typeof data !== 'object') return
    if (data.type === 'message' && data.message) {
      if (!activeTicketId || String(data.ticket_id) === String(activeTicketId)) {
        mergeMessage(data.message)
        // Incoming message implies peer stopped composing
        if (data.message.is_staff_reply !== !!options.isStaff) {
          clearPeerTyping()
        }
      }
    } else if (data.type === 'typing') {
      if (String(data.ticket_id) !== String(activeTicketId)) return
      if (sameUser(data.user_id, auth.user?.id)) return
      // Role filter: only care about peer side
      if (options.isStaff && data.is_staff) return
      if (!options.isStaff && !data.is_staff) return
      if (data.is_typing === true || data.is_typing === 'true' || data.is_typing === 1) {
        updateTyping([
          {
            user_id: data.user_id,
            name: data.name,
            is_staff: !!data.is_staff,
          },
        ])
      } else {
        // Explicit stop
        clearPeerTyping()
      }
    } else if (data.type === 'presence') {
      if (String(data.ticket_id) !== String(activeTicketId)) return
      if (data.role === 'staff') {
        presence.value = {
          ...presence.value,
          staff_online: !!data.online,
          staff_name: data.name || presence.value.staff_name,
          staff_last_seen: data.at,
        }
        // Peer left chat → clear typing
        if (!data.online && !options.isStaff) clearPeerTyping()
      } else {
        presence.value = {
          ...presence.value,
          user_online: !!data.online,
          user_name: data.name || presence.value.user_name,
          user_last_seen: data.at,
        }
        if (!data.online && options.isStaff) clearPeerTyping()
      }
    } else if (data.type === 'receipts') {
      if (String(data.ticket_id) !== String(activeTicketId)) return
      applyReceiptIds(data.message_ids || [], data.status, data.at)
    } else if (data.type === 'joined') {
      presence.value = data.presence || {}
      updateTyping(data.typing || [])
    } else if (data.type === 'connected') {
      connected.value = true
    }
  }

  function stopPoll() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  async function pollOnce() {
    if (!activeTicketId || destroyed || pollInFlight) return
    pollInFlight = true
    try {
      if (options.isStaff) {
        const { data } = await api.staffTicketAction(activeTicketId, {
          action: 'poll',
          since: sinceIso || undefined,
        })
        const payload = data as any
        for (const m of payload.messages || []) mergeMessage(m)
        applyReceipts(payload.receipts || [])
        // Poll is source of truth for typing — empty list clears sticky UI
        updateTyping(payload.typing || [])
        presence.value = payload.presence || presence.value
      } else {
        const { data } = await api.supportPoll(activeTicketId, sinceIso || undefined)
        for (const m of data.messages || []) mergeMessage(m)
        applyReceipts(data.receipts || [])
        updateTyping(data.typing || [])
        presence.value = data.presence || presence.value
      }
      connected.value = true
      if (mode.value !== 'ws') mode.value = 'poll'
    } catch {
      connected.value = false
    } finally {
      pollInFlight = false
    }
  }

  function startPoll() {
    stopPoll()
    if (mode.value === 'idle') mode.value = 'poll'
    pollOnce()
    pollTimer = setInterval(pollOnce, 1200)
  }

  function connectWs() {
    if (destroyed || !activeTicketId) return
    try {
      ws = new WebSocket(wsUrl(auth.token))
    } catch {
      return
    }
    ws.onopen = () => {
      mode.value = 'ws'
      connected.value = true
      ws?.send(JSON.stringify({ action: 'join', ticket_id: activeTicketId }))
      if (heartbeatTimer) clearInterval(heartbeatTimer)
      heartbeatTimer = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'heartbeat' }))
          ws.send(JSON.stringify({ action: 'mark_read' }))
        }
      }, 15000)
    }
    ws.onmessage = (ev) => {
      try {
        handleEvent(JSON.parse(ev.data))
      } catch { /* */ }
    }
    ws.onerror = () => { /* poll covers us */ }
    ws.onclose = () => {
      if (mode.value === 'ws') mode.value = 'poll'
    }
  }

  function onPageHide() {
    if (activeTicketId) notifyLeave(activeTicketId)
  }

  function join(ticketId: string, messages: Ref<TicketMessage[]>) {
    leave()
    destroyed = false
    activeTicketId = ticketId
    setMessagesRef(messages)
    const list = messages.value || []
    sinceIso = list.length ? list[list.length - 1].created_at : null
    clearPeerTyping()
    startPoll()
    connectWs()
    window.addEventListener('pagehide', onPageHide)
    window.addEventListener('beforeunload', onPageHide)
  }

  function notifyLeave(ticketId: string) {
    try {
      const token = auth.token
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      }
      if (token) headers.Authorization = `Token ${token}`
      const csrf = document.cookie
        .split(';')
        .map((c) => c.trim())
        .find((c) => c.startsWith('csrftoken='))
      if (csrf) headers['X-CSRFToken'] = decodeURIComponent(csrf.split('=').slice(1).join('='))

      if (options.isStaff) {
        const body = JSON.stringify({ action: 'leave' })
        fetch(`/api/v1/staff/tickets/${ticketId}/`, {
          method: 'POST',
          body,
          headers,
          credentials: 'same-origin',
          keepalive: true,
        }).catch(() => {})
      } else {
        fetch(`/api/v1/support/${ticketId}/leave/`, {
          method: 'POST',
          body: '{}',
          headers,
          credentials: 'same-origin',
          keepalive: true,
        }).catch(() => {})
      }
    } catch { /* */ }
  }

  function leave() {
    const tid = activeTicketId
    window.removeEventListener('pagehide', onPageHide)
    window.removeEventListener('beforeunload', onPageHide)
    if (typingTimer) clearTimeout(typingTimer)
    typingTimer = null
    if (typingPulse) {
      clearInterval(typingPulse)
      typingPulse = null
    }
    if (lastTypingSent && tid) {
      sendTyping(false)
    }
    lastTypingSent = false
    stopPoll()
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
    if (tid) {
      notifyLeave(tid)
    }
    if (ws) {
      try {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'leave' }))
        }
        ws.close()
      } catch { /* */ }
      ws = null
    }
    activeTicketId = null
    mode.value = 'idle'
    clearPeerTyping()
    presence.value = {}
  }

  function sendTyping(isTyping: boolean) {
    if (!activeTicketId) return
    // Avoid spamming identical state
    if (lastTypingSent === isTyping && isTyping) {
      // still refresh server TTL when pulse says keep-alive
    }
    lastTypingSent = isTyping
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'typing', is_typing: !!isTyping }))
    }
    if (options.isStaff) {
      api.staffTicketAction(activeTicketId, { action: 'typing', is_typing: !!isTyping }).catch(() => {})
    } else {
      api.supportTyping(activeTicketId, !!isTyping).catch(() => {})
    }
  }

  /** Call on every keystroke — keeps typing flag alive while composing. */
  function onComposerInput() {
    if (!activeTicketId) return
    sendTyping(true)
    if (typingTimer) clearTimeout(typingTimer)
    if (!typingPulse) {
      typingPulse = setInterval(() => {
        if (lastTypingSent) sendTyping(true)
      }, 2000)
    }
    // Idle → stop typing quickly so peer UI does not stick
    typingTimer = setTimeout(() => {
      sendTyping(false)
      if (typingPulse) {
        clearInterval(typingPulse)
        typingPulse = null
      }
    }, 1500)
  }

  function markRead() {
    if (!activeTicketId) return
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'mark_read' }))
    }
    if (!options.isStaff) {
      api.supportMarkRead(activeTicketId).catch(() => {})
    } else {
      api.staffTicketAction(activeTicketId, { action: 'heartbeat' }).catch(() => {})
    }
  }

  onUnmounted(() => {
    destroyed = true
    leave()
  })

  // reactive() auto-unwraps nested refs in templates (plain objects do not).
  // Without this, v-if="chat.peerTypingText" is always true (Ref object is truthy).
  return reactive({
    connected,
    mode,
    typing,
    presence,
    peerTypingText,
    join,
    leave,
    onComposerInput,
    sendTyping,
    markRead,
    mergeMessage,
    receiptOf,
    pollOnce,
    clearPeerTyping,
  })
}
