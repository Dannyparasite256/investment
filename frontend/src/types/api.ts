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
  date_joined: string
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
