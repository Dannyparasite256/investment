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
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard',
      },
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
        path: 'markets',
        name: 'markets',
        component: () => import('@/views/MarketsView.vue'),
        meta: { title: 'Markets' },
      },
      {
        path: 'notifications',
        name: 'notifications',
        component: () => import('@/views/NotificationsView.vue'),
        meta: { title: 'Notifications' },
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/ProfileView.vue'),
        meta: { title: 'Profile' },
      },
      {
        path: 'referrals',
        name: 'referrals',
        component: () => import('@/views/ReferralsView.vue'),
        meta: { title: 'Referrals' },
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
  return true
})

router.afterEach((to) => {
  const ui = useUiStore()
  ui.setLoading(false)
  const title = (to.meta.title as string) || 'CryptoInvest'
  document.title = `${title} · CryptoInvest`
})

export default router
