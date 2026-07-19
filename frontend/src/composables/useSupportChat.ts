/**
 * Realtime support chat: WebSocket when available, HTTP poll fallback.
 * Handles typing, presence, and delivery/read receipt merges.
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
  let lastTypingSent = false
  let activeTicketId: string | null = null
  let sinceIso: string | null = null
  let destroyed = false
  let messagesRef: Ref<TicketMessage[]> | null = null

  function setMessagesRef(r: Ref<TicketMessage[]>) {
    messagesRef = r
  }

  function mergeMessage(m: TicketMessage) {
    if (!messagesRef) return
    const list = messagesRef.value
    const idx = list.findIndex((x) => x.id === m.id)
    if (idx >= 0) {
      list[idx] = { ...list[idx], ...m, _pending: false, _failed: false }
    } else {
      // Drop matching optimistic pending by body
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
    const map = new Map(receipts.map((r) => [r.id, r]))
    messagesRef.value = messagesRef.value.map((m) => {
      const r = map.get(m.id)
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
    const names = list.map((t) => (t.is_staff ? 'Support' : t.name || 'User'))
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
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  function startPoll() {
    stopPoll()
    mode.value = 'poll'
    const tick = async () => {
      if (!activeTicketId || destroyed) return
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
      } catch {
        connected.value = false
      }
    }
    tick()
    pollTimer = setInterval(tick, 2500)
  }

  function connectWs() {
    if (destroyed || !activeTicketId) return
    try {
      ws = new WebSocket(wsUrl(auth.token))
    } catch {
      startPoll()
      return
    }
    let opened = false
    const failTimer = setTimeout(() => {
      if (!opened) {
        try {
          ws?.close()
        } catch { /* */ }
        startPoll()
      }
    }, 2500)

    ws.onopen = () => {
      opened = true
      clearTimeout(failTimer)
      mode.value = 'ws'
      connected.value = true
      ws?.send(JSON.stringify({ action: 'join', ticket_id: activeTicketId }))
      stopPoll()
      // Light poll still for receipt safety if channel layer is in-memory multi-worker
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
    ws.onerror = () => {
      /* onclose handles fallback */
    }
    ws.onclose = () => {
      connected.value = false
      if (!destroyed && activeTicketId && mode.value === 'ws') {
        // fall back to polling
        startPoll()
      }
    }
  }

  function join(ticketId: string, messages: Ref<TicketMessage[]>) {
    leave()
    destroyed = false
    activeTicketId = ticketId
    setMessagesRef(messages)
    const list = messages.value || []
    if (list.length) {
      sinceIso = list[list.length - 1].created_at
    } else {
      sinceIso = null
    }
    connectWs()
    // Always run poll as reliable baseline (WS may not work on PA)
    startPoll()
  }

  function leave() {
    if (typingTimer) clearTimeout(typingTimer)
    if (lastTypingSent && activeTicketId) {
      sendTyping(false)
    }
    lastTypingSent = false
    stopPoll()
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
    if (isTyping === lastTypingSent && isTyping) {
      // refresh TTL
    }
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

  function onComposerInput() {
    sendTyping(true)
    if (typingTimer) clearTimeout(typingTimer)
    typingTimer = setTimeout(() => sendTyping(false), 1800)
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
  }
}
