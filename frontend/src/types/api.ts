export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  phone: string
  email_verified: boolean
  is_kyc_verified: boolean
  two_factor_enabled: boolean
  referral_code: string
  referral_earnings: string
  country: string
  country_code?: string
  date_joined: string
  preferred_theme?: string
  preferred_ui_theme?: string
  preferred_language?: string
  preferred_currency?: string
  preferred_timezone?: string
  email_alerts?: boolean
  sms_alerts?: boolean
  risk_score?: number
  tour_completed?: boolean
  is_staff?: boolean
  is_superuser?: boolean
  role?: string
  is_staff_panel?: boolean
  avatar_url?: string
  display_name?: string
}

export interface BalanceMoney {
  value: string
  symbol: string
  code?: string
  formatted: string
  usd_price?: number
  usd_equivalent?: string
  label: string
}

export interface DisplayBalances {
  ok?: boolean
  error?: string
  currency?: string
  message?: string
  saved?: boolean
  available?: BalanceMoney
  balance?: BalanceMoney
  profit?: BalanceMoney
  locked?: BalanceMoney
  referral?: BalanceMoney
  active_capital?: BalanceMoney
  total_deposited?: BalanceMoney
  total_withdrawn?: BalanceMoney
  total_invested?: BalanceMoney
  [key: string]: unknown
}

export interface CurrencyOption {
  code: string
  label: string
  symbol: string
  kind: string
  usd_price: string
  network?: string
}

export interface ReceiptData {
  kind: string
  id: string
  title: string
  status: string
  status_label: string
  display_currency: string
  currency_symbol: string
  amount: BalanceMoney
  fee?: BalanceMoney | null
  net?: BalanceMoney | null
  rows: Array<{ label: string; value: string }>
  print_url?: string
}

export interface Wallet {
  balance: string
  locked_balance: string
  available_balance: string
  total_deposited: string
  total_withdrawn: string
  total_profit: string
  total_invested: string
}

export interface Cryptocurrency {
  id: number
  symbol: string
  name: string
  network: string
  decimals: number
  min_deposit: string
  min_withdrawal: string
  max_withdrawal: string
  withdrawal_fee: string
  deposit_address: string
  is_active: boolean
  /** Emoji / glyph from backend (fallback when CDN image fails). */
  icon?: string
  /** Data URI or media URL for deposit address QR (when available). */
  qr?: string
}

export interface InvestmentPlan {
  id: string
  name: string
  slug: string
  description: string
  short_description: string
  min_deposit: string
  max_deposit: string
  duration_days: number
  profit_method: string
  profit_rate_percent: string
  return_percent_min: string
  return_percent_max: string
  expected_return: string
  payout_frequency: string
  risk_level: string
  status: string
  is_featured: boolean
  allow_auto_reinvest: boolean
  allow_manual_reinvest: boolean
  return_principal: boolean
}

export interface Investment {
  id: string
  plan: string
  plan_name: string
  amount: string
  status: string
  profit_rate_percent: string
  payout_frequency: string
  duration_days: number
  total_earned: string
  auto_reinvest: boolean
  payouts_count: number
  expected_payouts: number
  started_at: string
  matures_at: string
  completed_at: string | null
  progress_percent: number
  next_payout_at: string | null
}

export interface Deposit {
  id: string
  cryptocurrency: number
  crypto_symbol: string
  amount: string
  transaction_hash: string
  network: string
  status: string
  created_at: string
  reviewed_at: string | null
  rejection_reason: string
}

export interface Withdrawal {
  id: string
  cryptocurrency: number
  crypto_symbol: string
  amount: string
  fee: string
  net_amount: string
  wallet_address: string
  network: string
  status: string
  created_at: string
  rejection_reason: string
}

export interface Transaction {
  id: string
  tx_type: string
  amount: string
  status: string
  description: string
  created_at: string
  reference_type?: string
  reference_id?: string
  fee?: string
  currency?: string
}

export interface Earning {
  id: string
  investment: string
  amount: string
  period_number: number
  is_reinvested: boolean
  created_at: string
}

export interface AppNotification {
  id: string
  title: string
  message: string
  level: string
  category: string
  is_read: boolean
  link: string
  created_at: string
}

export interface SupportTicket {
  id: string
  subject: string
  category: string
  status: string
  priority: string
  created_at: string
  updated_at: string
  message_count?: number
  unread_count?: number
  messages?: TicketMessage[]
}

export type ReceiptStatus = 'pending' | 'sent' | 'delivered' | 'read'

export interface TicketReplyPreview {
  id: string
  body: string
  is_staff_reply: boolean
  sender_name: string
}

export interface TicketMessage {
  id: string
  body: string
  is_staff_reply: boolean
  created_at: string
  delivered_at?: string | null
  read_at?: string | null
  receipt_status?: ReceiptStatus | string
  sender: number
  sender_name: string
  attachment?: string | null
  attachment_url?: string | null
  reply_to_id?: string | null
  reply_to?: TicketReplyPreview | null
  /** Local optimistic flag before server ack */
  _pending?: boolean
  _failed?: boolean
  _localPreview?: string
}

export interface ChatPresence {
  user_online?: boolean
  staff_online?: boolean
  user_name?: string
  staff_name?: string
  user_last_seen?: string | null
  staff_last_seen?: string | null
}

export interface ChatTyper {
  user_id: number
  name: string
  is_staff: boolean
  at?: string
}

export interface ChatPollPayload {
  ticket_id?: string
  status?: string
  updated_at?: string
  messages: TicketMessage[]
  receipts?: TicketMessage[]
  typing: ChatTyper[]
  presence: ChatPresence
  server_time?: string
}

export interface WatchlistItem {
  id: string
  symbol: string
  label: string
  created_at: string
}

export interface PriceAlert {
  id: string
  symbol: string
  label: string
  target_price: string
  direction: string
  is_active: boolean
  triggered_at: string | null
  last_price: string | null
  created_at: string
}

export interface TradingSignal {
  id: string
  title: string
  symbol: string
  side: string
  entry_note: string
  target: string
  stop_loss: string
  created_at: string
}

export interface ActivityEvent {
  id: string
  event_type: string
  title: string
  description: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface VipTier {
  id: number
  name: string
  slug: string
  min_total_invested: string
  badge_color: string
  deposit_fee_percent: string
  withdrawal_fee_percent: string
  referral_bonus_boost: string
  sticker_emoji?: string
  sticker_tagline?: string
}

export interface VipMember {
  name: string
  email: string
  avatar_url: string
  initials: string
}

export interface VipStatus {
  tier: VipTier | null
  next_tier: VipTier | null
  total_invested: string
  progress_pct: number
  remaining: string
  sticker_emoji: string
  tiers: VipTier[]
  member?: VipMember
}

export interface PortfolioData {
  days: number
  equity_now: string
  labels: string[]
  equity: number[]
  profit: number[]
  active_investments: number
  total_earned: string
  disclaimer: string
}

export interface ReferralStats {
  total_referrals: number
  total_earned: string
  pending: string
  paid: string
  rate: string
  rate_l2: string
  rate_l3: string
  pays_on: string
}

export interface ReferralData {
  code: string
  link: string
  spa_link: string
  stats: ReferralStats
  referred: Array<{
    id: number
    email: string
    date_joined: string
    is_kyc_verified: boolean
  }>
  commissions: Array<{
    id: string
    amount: string
    rate_percent: string
    base_amount: string
    source: string
    level: number
    status: string
    created_at: string
    referred_email: string
  }>
}

export interface FAQItem {
  id: string
  question: string
  answer: string
  category: string
  sort_order: number
}

export interface KYCDocument {
  id: string
  document_type: string
  document_number: string
  front_image: string | null
  back_image: string | null
  selfie_image: string | null
  status: string
  rejection_reason: string
  created_at: string
}

export interface WalletAddress {
  id: string
  cryptocurrency: number
  crypto_symbol: string
  address: string
  label: string
  is_default: boolean
  is_verified: boolean
  created_at: string
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface AuthResponse {
  token: string
  user: User
}

export interface MeResponse {
  user: User
  wallet: Wallet
}

export interface LivePrices {
  prices?: Record<string, number | string>
  source?: string
  updated_at?: string
}

export interface DashboardStats {
  wallet: Wallet
  unread_notifications: number
  open_tickets: number
  active_investments: number
  pending_deposits: number
  pending_withdrawals: number
}

export interface SearchResult {
  type: string
  title: string
  subtitle: string
  path: string
}
