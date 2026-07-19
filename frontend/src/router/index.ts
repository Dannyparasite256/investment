import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { public: true, title: 'Log in' },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { public: true, title: 'Register' },
  },
  {
    path: '/join',
    name: 'join',
    component: () => import('@/views/JoinView.vue'),
    meta: { public: true, title: 'Join' },
  },
  {
    path: '/join/:code',
    name: 'join-code',
    component: () => import('@/views/JoinView.vue'),
    meta: { public: true, title: 'Join' },
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: 'Dashboard' },
      },
      {
        path: 'plans',
        name: 'plans',
        component: () => import('@/views/PlansView.vue'),
        meta: { title: 'Investment Plans' },
      },
      {
        path: 'plans/:slug',
        name: 'plan-detail',
        component: () => import('@/views/PlanDetailView.vue'),
        meta: { title: 'Plan' },
      },
      {
        path: 'investments',
        name: 'investments',
        component: () => import('@/views/InvestmentsView.vue'),
        meta: { title: 'My Investments' },
      },
      {
        path: 'investments/:id',
        name: 'investment-detail',
        component: () => import('@/views/InvestmentDetailView.vue'),
        meta: { title: 'Investment' },
      },
      {
        path: 'calculator',
        name: 'calculator',
        component: () => import('@/views/CalculatorView.vue'),
        meta: { title: 'Calculator' },
      },
      {
        path: 'portfolio',
        name: 'portfolio',
        component: () => import('@/views/PortfolioView.vue'),
        meta: { title: 'Performance' },
      },
      {
        path: 'wallet',
        name: 'wallet',
        component: () => import('@/views/WalletView.vue'),
        meta: { title: 'Wallet' },
      },
      {
        path: 'deposits',
        name: 'deposits',
        component: () => import('@/views/DepositsView.vue'),
        meta: { title: 'Deposits' },
      },
      {
        path: 'withdrawals',
        name: 'withdrawals',
        component: () => import('@/views/WithdrawalsView.vue'),
        meta: { title: 'Withdrawals' },
      },
      {
        path: 'transactions',
        name: 'transactions',
        component: () => import('@/views/TransactionsView.vue'),
        meta: { title: 'Transactions' },
      },
      {
        path: 'earnings',
        name: 'earnings',
        component: () => import('@/views/EarningsView.vue'),
        meta: { title: 'Earnings' },
      },
      {
        path: 'statements',
        name: 'statements',
        component: () => import('@/views/StatementsView.vue'),
        meta: { title: 'Statements' },
      },
      {
        path: 'markets',
        name: 'markets',
        component: () => import('@/views/MarketsView.vue'),
        meta: { title: 'Markets' },
      },
      {
        path: 'watchlist',
        name: 'watchlist',
        component: () => import('@/views/WatchlistView.vue'),
        meta: { title: 'Watchlist' },
      },
      {
        path: 'alerts',
        name: 'alerts',
        component: () => import('@/views/AlertsView.vue'),
        meta: { title: 'Price Alerts' },
      },
      {
        path: 'signals',
        name: 'signals',
        component: () => import('@/views/SignalsView.vue'),
        meta: { title: 'Signals' },
      },
      {
        path: 'notifications',
        name: 'notifications',
        component: () => import('@/views/NotificationsView.vue'),
        meta: { title: 'Notifications' },
      },
      {
        path: 'activity',
        name: 'activity',
        component: () => import('@/views/ActivityView.vue'),
        meta: { title: 'Activity' },
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/ProfileView.vue'),
        meta: { title: 'Profile' },
      },
      {
        path: 'kyc',
        name: 'kyc',
        component: () => import('@/views/KycView.vue'),
        meta: { title: 'KYC' },
      },
      {
        path: 'security',
        name: 'security',
        component: () => import('@/views/SecurityView.vue'),
        meta: { title: 'Security' },
      },
      {
        path: 'referrals',
        name: 'referrals',
        component: () => import('@/views/ReferralsView.vue'),
        meta: { title: 'Referrals' },
      },
      {
        path: 'vip',
        name: 'vip',
        component: () => import('@/views/VipView.vue'),
        meta: { title: 'VIP' },
      },
      {
        path: 'goals',
        name: 'goals',
        component: () => import('@/views/GoalsView.vue'),
        meta: { title: 'Goals' },
      },
      {
        path: 'trust',
        name: 'trust',
        component: () => import('@/views/TrustView.vue'),
        meta: { title: 'Trust center' },
      },
      {
        path: 'announcements',
        name: 'announcements',
        component: () => import('@/views/AnnouncementsView.vue'),
        meta: { title: 'Announcements' },
      },
      {
        path: 'onboarding',
        name: 'onboarding',
        component: () => import('@/views/OnboardingView.vue'),
        meta: { title: 'Get started' },
      },
      {
        path: 'support',
        name: 'support',
        component: () => import('@/views/SupportView.vue'),
        meta: { title: 'Support' },
      },
      {
        path: 'support/:id',
        name: 'support-detail',
        component: () => import('@/views/SupportView.vue'),
        meta: { title: 'Support chat' },
      },
      {
        path: 'faq',
        name: 'faq',
        component: () => import('@/views/FaqView.vue'),
        meta: { title: 'FAQ' },
      },
      {
        path: 'risk-quiz',
        name: 'risk-quiz',
        component: () => import('@/views/RiskQuizView.vue'),
        meta: { title: 'Risk Profile' },
      },
      {
        path: 'search',
        name: 'search',
        component: () => import('@/views/SearchView.vue'),
        meta: { title: 'Search' },
      },
      {
        path: 'receipts/:kind/:id',
        name: 'receipt',
        component: () => import('@/views/ReceiptView.vue'),
        meta: { title: 'Receipt' },
      },
      // Staff / admin (requires is_staff_panel)
      {
        path: 'admin',
        name: 'admin',
        component: () => import('@/views/staff/StaffDashboardView.vue'),
        meta: { title: 'Admin', staff: true },
      },
      {
        path: 'admin/deposits',
        name: 'admin-deposits',
        component: () => import('@/views/staff/StaffDepositsView.vue'),
        meta: { title: 'Admin Deposits', staff: true },
      },
      {
        path: 'admin/withdrawals',
        name: 'admin-withdrawals',
        component: () => import('@/views/staff/StaffWithdrawalsView.vue'),
        meta: { title: 'Admin Withdrawals', staff: true },
      },
      {
        path: 'admin/kyc',
        name: 'admin-kyc',
        component: () => import('@/views/staff/StaffKycView.vue'),
        meta: { title: 'Admin KYC', staff: true },
      },
      {
        path: 'admin/users',
        name: 'admin-users',
        component: () => import('@/views/staff/StaffUsersView.vue'),
        meta: { title: 'Admin Users', staff: true },
      },
      {
        path: 'admin/tickets',
        name: 'admin-tickets',
        component: () => import('@/views/staff/StaffTicketsView.vue'),
        meta: { title: 'Support chat', staff: true },
      },
      {
        path: 'admin/tickets/:id',
        name: 'admin-ticket-detail',
        component: () => import('@/views/staff/StaffTicketsView.vue'),
        meta: { title: 'Support chat', staff: true },
      },
      {
        path: 'admin/fraud',
        name: 'admin-fraud',
        component: () => import('@/views/staff/StaffFraudView.vue'),
        meta: { title: 'Fraud signals', staff: true },
      },
      {
        path: 'admin/broadcast',
        name: 'admin-broadcast',
        component: () => import('@/views/staff/StaffBroadcastView.vue'),
        meta: { title: 'Bulk notify', staff: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { public: true, title: 'Not found' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  const ui = useUiStore()
  ui.setLoading(true)
  ui.closeSidebar()

  if (auth.token && !auth.user) {
    await auth.fetchMe()
  }

  if (to.meta.requiresAuth !== false && !to.meta.public && !auth.isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } }
  }
  if ((to.name === 'login' || to.name === 'register') && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
  if (to.meta.staff && !auth.user?.is_staff_panel) {
    return { name: 'dashboard' }
  }
  return true
})

router.afterEach((to) => {
  const ui = useUiStore()
  ui.setLoading(false)
  const title = (to.meta.title as string) || 'CryptoInvest'
  document.title = `${title} · CryptoInvest`
})

export default router
