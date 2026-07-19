/** WhatsApp-style chat helpers shared by Support + Staff views. */

export function dayKey(iso?: string | null): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`
  } catch {
    return ''
  }
}

/** Today / Yesterday / full date — WhatsApp day pills */
export function dayLabel(iso?: string | null): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    const now = new Date()
    const startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const startMsg = new Date(d.getFullYear(), d.getMonth(), d.getDate())
    const diffDays = Math.round((startToday.getTime() - startMsg.getTime()) / 86400000)
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays > 1 && diffDays < 7) {
      return d.toLocaleDateString(undefined, { weekday: 'long' })
    }
    return d.toLocaleDateString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: d.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    })
  } catch {
    return ''
  }
}

export function truncatePreview(text: string, max = 72): string {
  const t = (text || '').replace(/\s+/g, ' ').trim()
  if (!t) return ''
  return t.length > max ? `${t.slice(0, max)}…` : t
}

export function isImageUrl(url: string): boolean {
  const u = (url || '').toLowerCase()
  return /\.(png|jpe?g|gif|webp|bmp)(\?|$)/i.test(u) || u.startsWith('blob:')
}

export async function copyText(text: string): Promise<boolean> {
  const t = (text || '').trim()
  if (!t) return false
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(t)
      return true
    }
  } catch { /* fall through */ }
  try {
    const ta = document.createElement('textarea')
    ta.value = t
    ta.style.position = 'fixed'
    ta.style.left = '-9999px'
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    return ok
  } catch {
    return false
  }
}
