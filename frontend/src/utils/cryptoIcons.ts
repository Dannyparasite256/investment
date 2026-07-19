/** Brand colors + glyph/CDN helpers for cryptocurrency UI badges. */

const BRAND: Record<string, { color: string; glyph: string; slug: string }> = {
  BTC: { color: '#F7931A', glyph: '₿', slug: 'btc' },
  ETH: { color: '#627EEA', glyph: 'Ξ', slug: 'eth' },
  USDT: { color: '#26A17B', glyph: '₮', slug: 'usdt' },
  USDC: { color: '#2775CA', glyph: '$', slug: 'usdc' },
  BNB: { color: '#F3BA2F', glyph: '◆', slug: 'bnb' },
  LTC: { color: '#345D9D', glyph: 'Ł', slug: 'ltc' },
  TRX: { color: '#FF0013', glyph: 'T', slug: 'trx' },
  XRP: { color: '#23292F', glyph: '✕', slug: 'xrp' },
  SOL: { color: '#9945FF', glyph: '◎', slug: 'sol' },
  DOGE: { color: '#C2A633', glyph: 'Ð', slug: 'doge' },
  MATIC: { color: '#8247E5', glyph: 'M', slug: 'matic' },
  POL: { color: '#8247E5', glyph: 'P', slug: 'matic' },
  AVAX: { color: '#E84142', glyph: 'A', slug: 'avax' },
  ADA: { color: '#0033AD', glyph: '₳', slug: 'ada' },
  DOT: { color: '#E6007A', glyph: '●', slug: 'dot' },
  LINK: { color: '#2A5ADA', glyph: '⬡', slug: 'link' },
  SHIB: { color: '#FFA409', glyph: 'S', slug: 'shib' },
  DAI: { color: '#F5AC37', glyph: '◈', slug: 'dai' },
  BUSD: { color: '#F0B90B', glyph: 'B', slug: 'busd' },
  TON: { color: '#0098EA', glyph: '◆', slug: 'ton' },
}

/** Base ticker from composite symbols like USDT_TRC20 → USDT */
export function cryptoBase(symbol?: string | null): string {
  if (!symbol) return ''
  return symbol.split(/[_\s/-]/)[0].toUpperCase()
}

export function cryptoBrand(symbol?: string | null) {
  const base = cryptoBase(symbol)
  return (
    BRAND[base] || {
      color: '#64748B',
      glyph: base.slice(0, 1) || '?',
      slug: base.toLowerCase() || 'generic',
    }
  )
}

/** Official-style SVG from cryptocurrency-icons package (jsDelivr). */
export function cryptoIconUrl(symbol?: string | null): string {
  const { slug } = cryptoBrand(symbol)
  return `https://cdn.jsdelivr.net/npm/cryptocurrency-icons@0.18.1/svg/color/${slug}.svg`
}

export function cryptoGlyph(symbol?: string | null, fallbackIcon?: string | null): string {
  if (fallbackIcon && fallbackIcon.length <= 3 && !fallbackIcon.includes(' ')) {
    return fallbackIcon
  }
  return cryptoBrand(symbol).glyph
}

export function cryptoColor(symbol?: string | null): string {
  return cryptoBrand(symbol).color
}
