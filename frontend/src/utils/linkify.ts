/**
 * Detect URLs in plain text and turn them into safe HTML links.
 * Links always open in a new tab (target="_blank" rel="noopener noreferrer").
 */

const URL_RE =
  /((?:https?:\/\/|www\.)[^\s<]+[^\s<.,;:!?"')\]}])/gi

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function normalizeHref(raw: string): string {
  const trimmed = raw.replace(/[),.]+$/g, '') // keep trailing punct out of href in matcher
  if (/^https?:\/\//i.test(trimmed)) return trimmed
  if (/^www\./i.test(trimmed)) return `https://${trimmed}`
  return trimmed
}

/** Split trailing punctuation that often follows a URL. */
function splitUrlToken(token: string): { url: string; trail: string } {
  let url = token
  let trail = ''
  while (/[.,;:!?)"'\]]$/.test(url) && url.length > 1) {
    trail = url.slice(-1) + trail
    url = url.slice(0, -1)
  }
  return { url, trail }
}

/**
 * Convert plain message body to HTML with clickable links.
 * Safe for v-html (escapes first, then injects anchors).
 */
export function linkify(text: string | null | undefined): string {
  if (!text) return ''
  const escaped = escapeHtml(String(text))
  // Preserve newlines as <br>
  const withBreaks = escaped.replace(/\r\n|\n|\r/g, '<br>')

  return withBreaks.replace(URL_RE, (match) => {
    const { url, trail } = splitUrlToken(match)
    if (!url || url.length < 4) return match
    const href = normalizeHref(url)
    // Only allow http(s)
    if (!/^https?:\/\//i.test(href)) return match
    const safeHref = href.replace(/"/g, '%22')
    return (
      `<a class="chat-link" href="${safeHref}" target="_blank" rel="noopener noreferrer">${url}</a>${trail}`
    )
  })
}
