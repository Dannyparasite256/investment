/** Offline crypto brand badges — pure CSS/text, no CDN, no SVG images. */

export type CryptoBrand = {
  color: string
  /** ASCII letter always renders on every device */
  letter: string
  label: string
}

const BRAND: Record<string, CryptoBrand> = {
  BTC: { color: '#F7931A', letter: 'B', label: 'Bitcoin' },
  ETH: { color: '#627EEA', letter: 'E', label: 'Ethereum' },
  USDT: { color: '#26A17B', letter: 'T', label: 'Tether' },
  USDC: { color: '#2775CA', letter: 'C', label: 'USD Coin' },
  BNB: { color: '#F3BA2F', letter: 'N', label: 'BNB' },
  LTC: { color: '#345D9D', letter: 'L', label: 'Litecoin' },
  TRX: { color: '#FF0013', letter: 'R', label: 'TRON' },
  XRP: { color: '#23292F', letter: 'X', label: 'XRP' },
  SOL: { color: '#9945FF', letter: 'S', label: 'Solana' },
  DOGE: { color: '#C2A633', letter: 'D', label: 'Dogecoin' },
  MATIC: { color: '#8247E5', letter: 'M', label: 'Polygon' },
  POL: { color: '#8247E5', letter: 'P', label: 'Polygon' },
  AVAX: { color: '#E84142', letter: 'A', label: 'Avalanche' },
  ADA: { color: '#0033AD', letter: 'A', label: 'Cardano' },
  DOT: { color: '#E6007A', letter: 'D', label: 'Polkadot' },
  LINK: { color: '#2A5ADA', letter: 'K', label: 'Chainlink' },
  SHIB: { color: '#FFA409', letter: 'H', label: 'Shiba' },
  DAI: { color: '#F5AC37', letter: 'D', label: 'Dai' },
  BUSD: { color: '#F0B90B', letter: 'B', label: 'BUSD' },
  TON: { color: '#0098EA', letter: 'T', label: 'Toncoin' },
  USD: { color: '#16A34A', letter: '$', label: 'US Dollar' },
  EUR: { color: '#2563EB', letter: '€', label: 'Euro' },
  GBP: { color: '#7C3AED', letter: '£', label: 'Pound' },
  UGX: { color: '#DC2626', letter: 'U', label: 'Uganda Shilling' },
}

/** Base ticker from composite symbols like USDT_TRC20 → USDT */
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
    }
  )
}

export function cryptoGlyph(symbol?: string | null, fallbackIcon?: string | null): string {
  // Prefer single-char ASCII / emoji from API only if short and not a CSS class
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

/** Pixel size for badge */
export function cryptoSizePx(size: 'xs' | 'sm' | 'md' | 'lg' = 'md'): number {
  if (size === 'xs') return 20
  if (size === 'sm') return 26
  if (size === 'lg') return 40
  return 32
}
