/** Offline crypto brand badges (data-URI SVG — no CDN). */

export type CryptoBrand = {
  color: string
  letter: string
  label: string
}

const BRAND: Record<string, CryptoBrand> = {
  BTC: { color: '#F7931A', letter: '₿', label: 'Bitcoin' },
  ETH: { color: '#627EEA', letter: 'Ξ', label: 'Ethereum' },
  USDT: { color: '#26A17B', letter: '₮', label: 'Tether' },
  USDC: { color: '#2775CA', letter: '$', label: 'USD Coin' },
  BNB: { color: '#F3BA2F', letter: 'B', label: 'BNB' },
  LTC: { color: '#345D9D', letter: 'Ł', label: 'Litecoin' },
  TRX: { color: '#FF0013', letter: 'T', label: 'TRON' },
  XRP: { color: '#23292F', letter: 'X', label: 'XRP' },
  SOL: { color: '#9945FF', letter: 'S', label: 'Solana' },
  DOGE: { color: '#C2A633', letter: 'Ð', label: 'Dogecoin' },
  MATIC: { color: '#8247E5', letter: 'M', label: 'Polygon' },
  POL: { color: '#8247E5', letter: 'P', label: 'Polygon' },
  AVAX: { color: '#E84142', letter: 'A', label: 'Avalanche' },
  ADA: { color: '#0033AD', letter: '₳', label: 'Cardano' },
  DOT: { color: '#E6007A', letter: '●', label: 'Polkadot' },
  LINK: { color: '#2A5ADA', letter: '⬡', label: 'Chainlink' },
  SHIB: { color: '#FFA409', letter: 'S', label: 'Shiba' },
  DAI: { color: '#F5AC37', letter: '◈', label: 'Dai' },
  BUSD: { color: '#F0B90B', letter: 'B', label: 'BUSD' },
  TON: { color: '#0098EA', letter: '◆', label: 'Toncoin' },
  USD: { color: '#16A34A', letter: '$', label: 'US Dollar' },
  EUR: { color: '#2563EB', letter: '€', label: 'Euro' },
  GBP: { color: '#7C3AED', letter: '£', label: 'Pound' },
  UGX: { color: '#DC2626', letter: 'U', label: 'Uganda Shilling' },
}

/** Base ticker from composite symbols like USDT_TRC20 → USDT */
export function cryptoBase(symbol?: string | null): string {
  if (!symbol) return ''
  const raw = String(symbol).trim()
  // Prefer known brand prefixes for composites
  const upper = raw.toUpperCase()
  for (const key of Object.keys(BRAND).sort((a, b) => b.length - a.length)) {
    if (upper === key || upper.startsWith(`${key}_`) || upper.startsWith(`${key}-`) || upper.startsWith(`${key} `)) {
      return key
    }
  }
  return raw.split(/[_\s/-]/)[0].toUpperCase()
}

export function cryptoBrand(symbol?: string | null): CryptoBrand {
  const base = cryptoBase(symbol)
  return (
    BRAND[base] || {
      color: '#64748B',
      letter: (base.slice(0, 1) || '?').toUpperCase(),
      label: base || 'Crypto',
    }
  )
}

/** Circular brand badge as data-URI SVG (works offline / no external CDN). */
export function cryptoIconUrl(symbol?: string | null, fallbackIcon?: string | null): string {
  const brand = cryptoBrand(symbol)
  let letter = brand.letter
  if (fallbackIcon && fallbackIcon.length <= 3 && !fallbackIcon.includes('bi-') && !fallbackIcon.includes('pi-')) {
    letter = fallbackIcon
  }
  // Escape for SVG text
  const safe = letter
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
  const fontSize = letter.length > 1 ? 11 : 15
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">` +
    `<circle cx="16" cy="16" r="16" fill="${brand.color}"/>` +
    `<text x="16" y="16" dy="0.38em" text-anchor="middle" fill="#ffffff" ` +
    `font-family="Segoe UI, system-ui, -apple-system, sans-serif" font-size="${fontSize}" font-weight="700">${safe}</text>` +
    `</svg>`
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}

export function cryptoGlyph(symbol?: string | null, fallbackIcon?: string | null): string {
  if (fallbackIcon && fallbackIcon.length <= 3 && !fallbackIcon.includes(' ')) {
    return fallbackIcon
  }
  return cryptoBrand(symbol).letter
}

export function cryptoColor(symbol?: string | null): string {
  return cryptoBrand(symbol).color
}
