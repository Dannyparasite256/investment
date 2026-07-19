import http from './http'
import type {
  AppNotification,
  AuthResponse,
  Cryptocurrency,
  Deposit,
  Earning,
  Investment,
  InvestmentPlan,
  LivePrices,
  MeResponse,
  Paginated,
  Transaction,
  Wallet,
  Withdrawal,
} from '@/types/api'

export const api = {
  login(username: string, password: string) {
    return http.post<AuthResponse>('/api/v1/auth/token/', { username, password })
  },
  me() {
    return http.get<MeResponse>('/api/v1/me/')
  },
  wallet() {
    return http.get<Wallet>('/api/v1/wallet/')
  },
  balances(currency?: string) {
    const q = currency ? `?currency=${encodeURIComponent(currency)}` : ''
    return http.get(`/api/balances/${q}`)
  },
  plans() {
    return http.get<InvestmentPlan[] | Paginated<InvestmentPlan>>('/api/v1/plans/')
  },
  plan(slug: string) {
    return http.get<InvestmentPlan>(`/api/v1/plans/${slug}/`)
  },
  investments() {
    return http.get<Paginated<Investment>>('/api/v1/investments/')
  },
  createInvestment(payload: { plan_id: string; amount: string | number; auto_reinvest?: boolean; duration_days?: number }) {
    return http.post<Investment>('/api/v1/investments/create_investment/', payload)
  },
  cryptocurrencies() {
    return http.get<Cryptocurrency[]>('/api/v1/cryptocurrencies/')
  },
  deposits() {
    return http.get<Paginated<Deposit>>('/api/v1/deposits/')
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
  notifications() {
    return http.get<Paginated<AppNotification>>('/api/v1/notifications/')
  },
  markNotificationRead(id: string) {
    return http.post(`/api/v1/notifications/${id}/mark_read/`)
  },
  prices() {
    return http.get<LivePrices>('/api/prices/')
  },
}

export function unwrapList<T>(data: T[] | Paginated<T>): T[] {
  if (Array.isArray(data)) return data
  return data?.results ?? []
}
