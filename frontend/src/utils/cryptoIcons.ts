/** Real crypto logos (local SVGs) + letter fallbacks. */

export type CryptoBrand = {
  color: string
  letter: string
  label: string
  /** filename under /static/img/crypto/ and /crypto/ (SPA public) */
  slug: string
}

const BRAND: Record<string, CryptoBrand> = {
  BTC: { color: '#F7931A', letter: 'B', label: 'Bitcoin', slug: 'btc' },
  ETH: { color: '#627EEA', letter: 'E', label: 'Ethereum', slug: 'eth' },
  USDT: { color: '#26A17B', letter: 'T', label: 'Tether', slug: 'usdt' },
  USDC: { color: '#2775CA', letter: 'C', label: 'USD Coin', slug: 'usdc' },
  BNB: { color: '#F3BA2F', letter: 'N', label: 'BNB', slug: 'bnb' },
  LTC: { color: '#345D9D', letter: 'L', label: 'Litecoin', slug: 'ltc' },
  TRX: { color: '#FF0013', letter: 'R', label: 'TRON', slug: 'trx' },
  XRP: { color: '#23292F', letter: 'X', label: 'XRP', slug: 'xrp' },
  SOL: { color: '#9945FF', letter: 'S', label: 'Solana', slug: 'sol' },
  DOGE: { color: '#C2A633', letter: 'D', label: 'Dogecoin', slug: 'doge' },
  MATIC: { color: '#8247E5', letter: 'M', label: 'Polygon', slug: 'matic' },
  POL: { color: '#8247E5', letter: 'P', label: 'Polygon', slug: 'matic' },
  AVAX: { color: '#E84142', letter: 'A', label: 'Avalanche', slug: 'avax' },
  ADA: { color: '#0033AD', letter: 'A', label: 'Cardano', slug: 'ada' },
  DOT: { color: '#E6007A', letter: 'D', label: 'Polkadot', slug: 'dot' },
  LINK: { color: '#2A5ADA', letter: 'K', label: 'Chainlink', slug: 'link' },
  DAI: { color: '#F5AC37', letter: 'D', label: 'Dai', slug: 'dai' },
  BUSD: { color: '#F0B90B', letter: 'B', label: 'BUSD', slug: 'bnb' },
  TON: { color: '#0098EA', letter: 'T', label: 'Toncoin', slug: 'ton' },
  USD: { color: '#16A34A', letter: '$', label: 'US Dollar', slug: 'usdc' },
  EUR: { color: '#2563EB', letter: '€', label: 'Euro', slug: 'usdc' },
  GBP: { color: '#7C3AED', letter: '£', label: 'Pound', slug: 'usdc' },
  UGX: { color: '#DC2626', letter: 'U', label: 'Uganda Shilling', slug: 'usdc' },
}

/** Slugs we ship as local SVG files */
export const LOCAL_CRYPTO_SLUGS = new Set([
  'btc', 'eth', 'usdt', 'usdc', 'bnb', 'ltc', 'trx', 'sol',
  'doge', 'matic', 'avax', 'ada', 'dot', 'link', 'dai', 'xrp',
])

export function cryptoBase(symbol?: string | null): string {
  if (!symbol) return ''
  const raw = String(symbol).trim()
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
      slug: base.toLowerCase() || 'generic',
    }
  )
}

export function cryptoGlyph(symbol?: string | null, fallbackIcon?: string | null): string {
  if (
    fallbackIcon &&
    fallbackIcon.length <= 2 &&
    !fallbackIcon.includes('bi-') &&
    !fallbackIcon.includes('pi-') &&
    !fallbackIcon.includes(' ')
  ) {
    return fallbackIcon
  }
  return cryptoBrand(symbol).letter
}

export function cryptoColor(symbol?: string | null): string {
  return cryptoBrand(symbol).color
}

export function cryptoSizePx(size: 'xs' | 'sm' | 'md' | 'lg' = 'md'): number {
  if (size === 'xs') return 20
  if (size === 'sm') return 26
  if (size === 'lg') return 40
  return 32
}

/**
 * URL for real logo SVG.
 * - SPA (Vite /app/): /app/crypto/{slug}.svg from public/
 * - Classic Django: /static/img/crypto/{slug}.svg
 */
export function cryptoLogoUrl(symbol?: string | null, preferStatic = false): string | null {
  const { slug } = cryptoBrand(symbol)
  if (!LOCAL_CRYPTO_SLUGS.has(slug)) return null
  if (preferStatic) return `/static/img/crypto/${slug}.svg`
  // Vite base is /app/ in production build
  const base = (import.meta as any).env?.BASE_URL || '/'
  const prefix = base.endsWith('/') ? base.slice(0, -1) : base
  // Prefer SPA public folder when running under /app/
  if (typeof window !== 'undefined' && window.location.pathname.startsWith('/app')) {
    return `${prefix}/crypto/${slug}.svg`
  }
  return `/static/img/crypto/${slug}.svg`
}
