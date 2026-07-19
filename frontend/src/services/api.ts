import http from './http'
import type {
  ActivityEvent,
  AppNotification,
  AuthResponse,
  Cryptocurrency,
  DashboardStats,
  Deposit,
  Earning,
  FAQItem,
  Investment,
  InvestmentPlan,
  KYCDocument,
  LivePrices,
  MeResponse,
  Paginated,
  PortfolioData,
  PriceAlert,
  ReferralData,
  SearchResult,
  SupportTicket,
  TicketMessage,
  TradingSignal,
  Transaction,
  User,
  VipStatus,
  Wallet,
  WalletAddress,
  WatchlistItem,
  Withdrawal,
} from '@/types/api'

export const api = {
  // Auth
  login(username: string, password: string) {
    return http.post<AuthResponse>('/api/v1/auth/token/', { username, password })
  },
  register(payload: {
    email: string
    password: string
    first_name?: string
    last_name?: string
    referral_code?: string
  }) {
    return http.post<AuthResponse>('/api/v1/auth/register/', payload)
  },
  me() {
    return http.get<MeResponse>('/api/v1/me/')
  },
  profile() {
    return http.get<User>('/api/v1/profile/')
  },
  updateProfile(payload: Partial<User>) {
    return http.patch<User>('/api/v1/profile/', payload)
  },
  changePassword(current_password: string, new_password: string) {
    return http.post<{ detail: string; token: string }>('/api/v1/profile/password/', {
      current_password,
      new_password,
    })
  },

  // Wallet & money
  wallet() {
    return http.get<Wallet>('/api/v1/wallet/')
  },
  balances(currency?: string) {
    const q = currency ? `?currency=${encodeURIComponent(currency)}` : ''
    return http.get(`/api/balances/${q}`)
  },
  cryptocurrencies() {
    return http.get<Cryptocurrency[]>('/api/v1/cryptocurrencies/')
  },
  walletAddresses() {
    return http.get<Paginated<WalletAddress> | WalletAddress[]>('/api/v1/wallet-addresses/')
  },
  createWalletAddress(payload: { cryptocurrency: number; address: string; label?: string; is_default?: boolean }) {
    return http.post<WalletAddress>('/api/v1/wallet-addresses/', payload)
  },
  deleteWalletAddress(id: string) {
    return http.delete(`/api/v1/wallet-addresses/${id}/`)
  },
  feePreview(amount: string | number, cryptocurrency?: number) {
    return http.get('/api/v1/fee-preview/', {
      params: { amount, cryptocurrency },
    })
  },

  // Plans & investments
  plans() {
    return http.get<InvestmentPlan[] | Paginated<InvestmentPlan>>('/api/v1/plans/')
  },
  plan(slug: string) {
    return http.get<InvestmentPlan>(`/api/v1/plans/${slug}/`)
  },
  investments() {
    return http.get<Paginated<Investment>>('/api/v1/investments/')
  },
  investment(id: string) {
    return http.get<Investment>(`/api/v1/investments/${id}/`)
  },
  createInvestment(payload: {
    plan_id: string
    amount: string | number
    auto_reinvest?: boolean
    duration_days?: number
  }) {
    return http.post<Investment>('/api/v1/investments/create_investment/', payload)
  },
  calculatorPlans() {
    return http.get('/api/v1/calculator/')
  },
  calculate(payload: { amount: number | string; profit_rate_percent: number | string; duration_days: number }) {
    return http.post('/api/v1/calculator/', payload)
  },

  // Deposits / withdrawals / ledger
  deposits() {
    return http.get<Paginated<Deposit>>('/api/v1/deposits/')
  },
  deposit(id: string) {
    return http.get<Deposit>(`/api/v1/deposits/${id}/`)
  },
  createDeposit(formData: FormData) {
    return http.post<Deposit>('/api/v1/deposits/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  withdrawals() {
    return http.get<Paginated<Withdrawal>>('/api/v1/withdrawals/')
  },
  createWithdrawal(payload: { cryptocurrency: number; amount: string | number; wallet_address: string }) {
    return http.post<Withdrawal>('/api/v1/withdrawals/', payload)
  },
  transactions(params?: { tx_type?: string; status?: string; page?: number }) {
    return http.get<Paginated<Transaction>>('/api/v1/transactions/', { params })
  },
  earnings() {
    return http.get<Paginated<Earning>>('/api/v1/earnings/')
  },
  statements() {
    return http.get('/api/v1/statements/')
  },

  // Notifications
  notifications(params?: { page?: number }) {
    return http.get<Paginated<AppNotification>>('/api/v1/notifications/', { params })
  },
  markNotificationRead(id: string) {
    return http.post(`/api/v1/notifications/${id}/mark_read/`)
  },
  markAllNotificationsRead() {
    return http.post('/api/v1/notifications/mark_all_read/')
  },

  // Markets
  prices() {
    return http.get<LivePrices>('/api/prices/')
  },
  marketPairs() {
    return http.get('/api/v1/markets/pairs/')
  },

  // Referrals
  referrals() {
    return http.get<ReferralData>('/api/v1/referrals/')
  },
  leaderboard() {
    return http.get('/api/v1/referrals/leaderboard/')
  },

  // VIP / portfolio
  vip() {
    return http.get<VipStatus>('/api/v1/vip/')
  },
  portfolio(days = 30) {
    return http.get<PortfolioData>('/api/v1/portfolio/', { params: { days } })
  },

  // Watchlist / alerts / signals / activity
  watchlist() {
    return http.get<WatchlistItem[]>('/api/v1/watchlist/')
  },
  addWatchlist(payload: { symbol: string; label?: string }) {
    return http.post<WatchlistItem>('/api/v1/watchlist/', payload)
  },
  removeWatchlist(id: string) {
    return http.delete(`/api/v1/watchlist/${id}/`)
  },
  alerts() {
    return http.get<PriceAlert[]>('/api/v1/alerts/')
  },
  createAlert(payload: { symbol: string; label?: string; target_price: string | number; direction: string }) {
    return http.post<PriceAlert>('/api/v1/alerts/', payload)
  },
  deleteAlert(id: string) {
    return http.delete(`/api/v1/alerts/${id}/`)
  },
  signals() {
    return http.get<{ results: TradingSignal[]; disclaimer: string }>('/api/v1/signals/')
  },
  activity() {
    return http.get<Paginated<ActivityEvent> | ActivityEvent[]>('/api/v1/activity/')
  },

  // Support
  tickets() {
    return http.get<Paginated<SupportTicket>>('/api/v1/support/')
  },
  ticket(id: string) {
    return http.get<SupportTicket>(`/api/v1/support/${id}/`)
  },
  createTicket(payload: { subject: string; body: string; category?: string }) {
    return http.post<SupportTicket>('/api/v1/support/', payload)
  },
  replyTicket(id: string, body: string) {
    return http.post<TicketMessage>(`/api/v1/support/${id}/reply/`, { body })
  },

  // KYC
  kycList() {
    return http.get<Paginated<KYCDocument> | KYCDocument[]>('/api/v1/kyc/')
  },
  submitKyc(formData: FormData) {
    return http.post<KYCDocument>('/api/v1/kyc/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // CMS / FAQ / risk / search / stats
  faq() {
    return http.get<FAQItem[]>('/api/v1/faq/')
  },
  page(slug: string) {
    return http.get(`/api/v1/pages/${slug}/`)
  },
  riskQuiz() {
    return http.get('/api/v1/risk-quiz/')
  },
  submitRiskQuiz(answers: Record<string, number>) {
    return http.post('/api/v1/risk-quiz/', { answers })
  },
  search(q: string) {
    return http.get<{ results: SearchResult[] }>('/api/v1/search/', { params: { q } })
  },
  dashboardStats() {
    return http.get<DashboardStats>('/api/v1/dashboard-stats/')
  },
}

export function unwrapList<T>(data: T[] | Paginated<T> | undefined | null): T[] {
  if (!data) return []
  if (Array.isArray(data)) return data
  return data.results ?? []
}
