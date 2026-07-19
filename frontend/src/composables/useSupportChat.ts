/**
 * Realtime support chat: HTTP poll is always the source of truth
 * (works on PythonAnywhere). WebSocket is optional bonus.
 */
import { onUnmounted, ref, type Ref } from 'vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type {
  ChatPresence,
  ChatTyper,
  ReceiptStatus,
  TicketMessage,
} from '@/types/api'

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
  let lastTypingSent = false
  let activeTicketId: string | null = null
  let sinceIso: string | null = null
  let destroyed = false
  let messagesRef: Ref<TicketMessage[]> | null = null
  let pollInFlight = false

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

  function updateTyping(list: ChatTyper[]) {
    typing.value = list || []
    if (!list?.length) {
      peerTypingText.value = ''
      return
    }
    const names = list.map((t) => (t.is_staff ? 'Support' : t.name || 'Customer'))
    peerTypingText.value =
      names.length === 1 ? `${names[0]} is typing…` : `${names.join(', ')} are typing…`
  }

  function handleEvent(data: any) {
    if (!data || typeof data !== 'object') return
    if (data.type === 'message' && data.message) {
      if (!activeTicketId || String(data.ticket_id) === String(activeTicketId)) {
        mergeMessage(data.message)
      }
    } else if (data.type === 'typing') {
      if (String(data.ticket_id) !== String(activeTicketId)) return
      if (data.user_id === auth.user?.id) return
      if (data.is_typing) {
        updateTyping([
          {
            user_id: data.user_id,
            name: data.name,
            is_staff: data.is_staff,
          },
        ])
      } else {
        updateTyping([])
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
      } else {
        presence.value = {
          ...presence.value,
          user_online: !!data.online,
          user_name: data.name || presence.value.user_name,
          user_last_seen: data.at,
        }
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
    // Fast poll so typing appears within ~1s
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
      // Keep HTTP poll running — WS alone is unreliable on multi-worker hosts
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
    // Poll is primary; WS is optional
    startPoll()
    connectWs()
    window.addEventListener('pagehide', onPageHide)
    window.addEventListener('beforeunload', onPageHide)
  }

  function notifyLeave(ticketId: string) {
    // Prefer sendBeacon so leave still fires on tab close / navigation
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
        if (navigator.sendBeacon) {
          // sendBeacon can't set auth headers easily — fall through to fetch keepalive
        }
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
    typing.value = []
    peerTypingText.value = ''
    presence.value = {}
  }

  function sendTyping(isTyping: boolean) {
    if (!activeTicketId) return
    lastTypingSent = isTyping
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'typing', is_typing: isTyping }))
    }
    if (options.isStaff) {
      api.staffTicketAction(activeTicketId, { action: 'typing', is_typing: isTyping }).catch(() => {})
    } else {
      api.supportTyping(activeTicketId, isTyping).catch(() => {})
    }
  }

  /** Call on every keystroke — keeps typing flag alive while composing. */
  function onComposerInput() {
    if (!activeTicketId) return
    sendTyping(true)
    if (typingTimer) clearTimeout(typingTimer)
    // Refresh TTL every 2s while still typing
    if (!typingPulse) {
      typingPulse = setInterval(() => {
        if (lastTypingSent) sendTyping(true)
      }, 2500)
    }
    typingTimer = setTimeout(() => {
      sendTyping(false)
      if (typingPulse) {
        clearInterval(typingPulse)
        typingPulse = null
      }
    }, 2000)
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

  return {
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
  }
}
