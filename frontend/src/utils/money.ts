export function formatMoney(value: string | number | null | undefined, places = 2): string {
  if (value === null || value === undefined || value === '') return places === 0 ? '0' : '0.00'
  const n = typeof value === 'number' ? value : parseFloat(String(value).replace(/,/g, ''))
  if (Number.isNaN(n)) return String(value)
  return n.toLocaleString('en-US', {
    minimumFractionDigits: places,
    maximumFractionDigits: places,
  })
}

export function shortDate(iso?: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

export function statusSeverity(status: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' {
  const s = (status || '').toLowerCase()
  if (['approved', 'completed', 'paid', 'active', 'success'].includes(s)) return 'success'
  if (['pending', 'processing', 'waiting_confirmation', 'under_review'].includes(s)) return 'warn'
  if (['rejected', 'failed', 'cancelled'].includes(s)) return 'danger'
  return 'info'
}
