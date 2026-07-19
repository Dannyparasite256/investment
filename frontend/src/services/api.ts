import http from './http'
import type {
  ActivityEvent,
  AppNotification,
  AuthResponse,
  ChatPollPayload,
  Cryptocurrency,
  CurrencyOption,
  DashboardStats,
  Deposit,
  DisplayBalances,
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
  ReceiptData,
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
  currencies() {
    return http.get<{ current: string; meta: any; options: CurrencyOption[] }>('/api/v1/currencies/')
  },
  balances(currency?: string) {
    return http.get<DisplayBalances>('/api/v1/balances/', {
      params: currency ? { currency } : undefined,
    })
  },
  setDisplayCurrency(currency: string) {
    return http.post<DisplayBalances>('/api/v1/display-currency/', { currency })
  },
  depositReceipt(id: string) {
    return http.get<ReceiptData>(`/api/v1/receipts/deposit/${id}/`)
  },
  withdrawalReceipt(id: string) {
    return http.get<ReceiptData>(`/api/v1/receipts/withdrawal/${id}/`)
  },
  transactionReceipt(id: string) {
    return http.get<ReceiptData>(`/api/v1/receipts/transaction/${id}/`)
  },
  investmentReceipt(id: string) {
    return http.get<ReceiptData>(`/api/v1/receipts/investment/${id}/`)
  },
  earningReceipt(id: string) {
    return http.get<ReceiptData>(`/api/v1/receipts/earning/${id}/`)
  },
  referralReceipt(id: string) {
    return http.get<ReceiptData>(`/api/v1/receipts/referral/${id}/`)
  },

  // Staff admin
  staffDashboard() {
    return http.get('/api/v1/staff/dashboard/')
  },
  staffDeposits(params?: { status?: string; q?: string }) {
    return http.get('/api/v1/staff/deposits/', { params })
  },
  staffDepositAction(id: string, action: 'approve' | 'reject', payload?: { notes?: string; reason?: string }) {
    return http.post(`/api/v1/staff/deposits/${id}/${action}/`, payload || {})
  },
  staffWithdrawals(params?: { status?: string; q?: string }) {
    return http.get('/api/v1/staff/withdrawals/', { params })
  },
  staffWithdrawalAction(
    id: string,
    action: 'approve' | 'paid' | 'reject',
    payload?: { notes?: string; reason?: string; tx_hash?: string },
  ) {
    return http.post(`/api/v1/staff/withdrawals/${id}/${action}/`, payload || {})
  },
  staffKyc(params?: { status?: string }) {
    return http.get('/api/v1/staff/kyc/', { params })
  },
  staffKycAction(id: string, action: 'approve' | 'reject', payload?: { reason?: string }) {
    return http.post(`/api/v1/staff/kyc/${id}/${action}/`, payload || {})
  },
  staffUsers(params?: { q?: string }) {
    return http.get('/api/v1/staff/users/', { params })
  },
  staffTickets() {
    return http.get('/api/v1/staff/tickets/')
  },
  staffTicket(id: string) {
    return http.get(`/api/v1/staff/tickets/${id}/`)
  },
  staffTicketReply(id: string, body: string, file?: File | null, replyToId?: string | null) {
    if (file || replyToId) {
      const fd = new FormData()
      if (body) fd.append('body', body)
      if (file) fd.append('attachment', file)
      if (replyToId) fd.append('reply_to', replyToId)
      return http.post(`/api/v1/staff/tickets/${id}/`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    }
    return http.post(`/api/v1/staff/tickets/${id}/`, { body })
  },
  staffTicketAction(id: string, payload: Record<string, unknown>) {
    return http.post(`/api/v1/staff/tickets/${id}/`, payload)
  },
  staffTicketStatus(id: string, status: string) {
    return http.post(`/api/v1/staff/tickets/${id}/`, { action: 'status', status })
  },
  staffTicketMute(id: string, muted: boolean) {
    return http.post(`/api/v1/staff/tickets/${id}/`, { action: 'mute', muted })
  },
  staffTicketPin(id: string, pinned: boolean) {
    return http.post(`/api/v1/staff/tickets/${id}/`, { action: 'pin', pinned })
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
  statements(params?: { format?: 'json' | 'csv' | 'pdf'; from?: string; to?: string }) {
    const fmt = params?.format || 'json'
    if (fmt === 'pdf' || fmt === 'csv') {
      return http.get('/api/v1/statements/', {
        params,
        responseType: 'blob' as any,
      })
    }
    return http.get('/api/v1/statements/', { params })
  },
  pushUnsubscribe(endpoint: string) {
    return http.delete('/api/v1/push/subscribe/', { data: { endpoint } })
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
  leaderboard(params?: { season?: string }) {
    return http.get('/api/v1/referrals/leaderboard/', { params })
  },

  // VIP / portfolio
  vip() {
    return http.get<VipStatus>('/api/v1/vip/')
  },
  portfolio(days = 30) {
    return http.get<PortfolioData>('/api/v1/portfolio/', { params: { days } })
  },
  patchInvestment(id: string, payload: { auto_reinvest?: boolean }) {
    return http.patch(`/api/v1/investments/${id}/`, payload)
  },

  // Feature pack
  bootstrap() {
    return http.get('/api/v1/bootstrap/')
  },
  announcements() {
    return http.get<{ results: any[] }>('/api/v1/announcements/')
  },
  completeTour() {
    return http.post('/api/v1/tour/complete/')
  },
  socialProof() {
    return http.get<{ results: any[] }>('/api/v1/social-proof/')
  },
  validatePromo(code: string, amount?: string | number) {
    return http.post('/api/v1/promos/validate/', { code, amount })
  },
  goals() {
    return http.get<{ results: any[] }>('/api/v1/goals/')
  },
  createGoal(payload: { title: string; target_amount: string | number; deadline?: string; notes?: string }) {
    return http.post('/api/v1/goals/', payload)
  },
  deleteGoal(id: string) {
    return http.delete(`/api/v1/goals/${id}/`)
  },
  calcScenarios() {
    return http.get<{ results: any[] }>('/api/v1/calculator/scenarios/')
  },
  saveCalcScenario(payload: { label: string; amount: string | number; rate_percent: string | number; duration_days: number }) {
    return http.post('/api/v1/calculator/scenarios/', payload)
  },
  pushSubscribe(payload: { endpoint: string; keys?: { p256dh?: string; auth?: string } }) {
    return http.post('/api/v1/push/subscribe/', payload)
  },
  trust() {
    return http.get('/api/v1/trust/')
  },
  supportTriage(q?: string) {
    return http.get('/api/v1/support/triage/', { params: q ? { q } : undefined })
  },
  ticketCsat(id: string, score: number, comment?: string) {
    return http.post(`/api/v1/support/${id}/csat/`, { score, comment })
  },
  staffCannedReplies() {
    return http.get('/api/v1/staff/canned-replies/')
  },
  staffFraud() {
    return http.get('/api/v1/staff/fraud/')
  },
  staffBroadcast(payload: { title: string; message: string; vip_slug?: string }) {
    return http.post('/api/v1/staff/broadcast/', payload)
  },
  staffExport(kind: string) {
    return http.get('/api/v1/staff/export/', { params: { kind }, responseType: 'blob' as any })
  },
  leaderboardSeason(season?: string) {
    return http.get('/api/v1/referrals/leaderboard/', { params: season ? { season } : undefined })
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
  replyTicket(id: string, body: string, file?: File | null, replyToId?: string | null) {
    if (file || replyToId) {
      const fd = new FormData()
      if (body) fd.append('body', body)
      if (file) fd.append('attachment', file)
      if (replyToId) fd.append('reply_to', replyToId)
      return http.post<TicketMessage>(`/api/v1/support/${id}/reply/`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    }
    return http.post<TicketMessage>(`/api/v1/support/${id}/reply/`, { body })
  },
  supportUnreadTotal() {
    return http.get<{ unread_count: number }>('/api/v1/support/unread_total/')
  },
  supportMute(id: string, muted: boolean) {
    return http.post(`/api/v1/support/${id}/mute/`, { muted })
  },
  supportPin(id: string, pinned: boolean) {
    return http.post(`/api/v1/support/${id}/pin/`, { pinned })
  },
  supportStarMessage(ticketId: string, msgId: string, starred: boolean) {
    return http.post(`/api/v1/support/${ticketId}/messages/${msgId}/star/`, { starred })
  },
  supportEditMessage(ticketId: string, msgId: string, body: string) {
    return http.post(`/api/v1/support/${ticketId}/messages/${msgId}/edit/`, { body })
  },
  supportDeleteMessage(ticketId: string, msgId: string) {
    return http.post(`/api/v1/support/${ticketId}/messages/${msgId}/delete/`, {})
  },
  supportCsat(ticketId: string, score: number, comment?: string) {
    return http.post(`/api/v1/support/${ticketId}/csat/`, { score, comment: comment || '' })
  },
  supportPoll(id: string, since?: string) {
    return http.get<ChatPollPayload>(`/api/v1/support/${id}/poll/`, {
      params: since ? { since } : undefined,
    })
  },
  supportTyping(id: string, is_typing: boolean) {
    return http.post(`/api/v1/support/${id}/typing/`, { is_typing })
  },
  supportHeartbeat(id: string) {
    return http.post(`/api/v1/support/${id}/heartbeat/`)
  },
  supportLeave(id: string) {
    return http.post(`/api/v1/support/${id}/leave/`)
  },
  supportMarkRead(id: string) {
    return http.post(`/api/v1/support/${id}/mark_read/`)
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
