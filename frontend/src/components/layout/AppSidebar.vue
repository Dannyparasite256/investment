<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { api } from '@/services/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const ui = useUiStore()
const supportUnread = ref(0)
let badgeTimer: ReturnType<typeof setInterval> | null = null

async function refreshSupportBadge() {
  try {
    const { data } = await api.supportUnreadTotal()
    supportUnread.value = data.unread_count || 0
  } catch { /* ignore */ }
}

onMounted(() => {
  refreshSupportBadge()
  badgeTimer = setInterval(refreshSupportBadge, 20000)
})
onUnmounted(() => {
  if (badgeTimer) clearInterval(badgeTimer)
})

const nav = computed(() => {
  const supportBadge = supportUnread.value > 0
    ? (supportUnread.value > 99 ? '99+' : String(supportUnread.value))
    : ''
  const sections = [
    {
      label: 'Main',
      items: [
        { to: '/dashboard', icon: 'pi pi-th-large', label: 'Dashboard', badge: '' },
        { to: '/plans', icon: 'pi pi-chart-line', label: 'Invest', badge: '' },
        { to: '/investments', icon: 'pi pi-briefcase', label: 'My Portfolio', badge: '' },
        { to: '/portfolio', icon: 'pi pi-chart-pie', label: 'Performance', badge: '' },
        { to: '/calculator', icon: 'pi pi-calculator', label: 'Calculator', badge: '' },
        { to: '/markets', icon: 'pi pi-chart-bar', label: 'Markets', badge: '' },
      ],
    },
    {
      label: 'Wallet',
      items: [
        { to: '/wallet', icon: 'pi pi-wallet', label: 'Wallet', badge: '' },
        { to: '/deposits', icon: 'pi pi-download', label: 'Deposit', badge: '' },
        { to: '/withdrawals', icon: 'pi pi-upload', label: 'Withdraw', badge: '' },
        { to: '/transactions', icon: 'pi pi-history', label: 'History', badge: '' },
        { to: '/earnings', icon: 'pi pi-dollar', label: 'Earnings', badge: '' },
        { to: '/statements', icon: 'pi pi-file', label: 'Statements', badge: '' },
      ],
    },
    {
      label: 'Markets tools',
      items: [
        { to: '/watchlist', icon: 'pi pi-star', label: 'Watchlist', badge: '' },
        { to: '/alerts', icon: 'pi pi-bell', label: 'Price alerts', badge: '' },
        { to: '/signals', icon: 'pi pi-bolt', label: 'Signals', badge: '' },
      ],
    },
    {
      label: 'Grow',
      items: [
        { to: '/referrals', icon: 'pi pi-users', label: 'Referrals', badge: '' },
        { to: '/vip', icon: 'pi pi-crown', label: 'VIP', badge: '' },
        { to: '/goals', icon: 'pi pi-flag', label: 'Goals', badge: '' },
        { to: '/onboarding', icon: 'pi pi-compass', label: 'Get started', badge: '' },
      ],
    },
    {
      label: 'Account',
      items: [
        { to: '/notifications', icon: 'pi pi-inbox', label: 'Notifications', badge: '' },
        { to: '/announcements', icon: 'pi pi-megaphone', label: 'Announcements', badge: '' },
        { to: '/activity', icon: 'pi pi-clock', label: 'Activity', badge: '' },
        { to: '/support', icon: 'pi pi-comments', label: 'Support chat', badge: supportBadge },
        { to: '/trust', icon: 'pi pi-verified', label: 'Trust center', badge: '' },
        { to: '/kyc', icon: 'pi pi-id-card', label: 'KYC', badge: '' },
        { to: '/security', icon: 'pi pi-shield', label: 'Security', badge: '' },
        { to: '/profile', icon: 'pi pi-user', label: 'Profile', badge: '' },
        { to: '/faq', icon: 'pi pi-question-circle', label: 'FAQ', badge: '' },
        { to: '/risk-quiz', icon: 'pi pi-sliders-h', label: 'Risk profile', badge: '' },
      ],
    },
  ]
  if (auth.user?.is_staff_panel) {
    sections.push({
      label: 'Admin',
      items: [
        { to: '/admin', icon: 'pi pi-cog', label: 'Admin home', badge: '' },
        { to: '/admin/deposits', icon: 'pi pi-check-circle', label: 'Approve deposits', badge: '' },
        { to: '/admin/withdrawals', icon: 'pi pi-send', label: 'Payouts', badge: '' },
        { to: '/admin/kyc', icon: 'pi pi-id-card', label: 'KYC review', badge: '' },
        { to: '/admin/users', icon: 'pi pi-users', label: 'Users', badge: '' },
        { to: '/admin/tickets', icon: 'pi pi-headphones', label: 'Support chat', badge: '' },
        { to: '/admin/fraud', icon: 'pi pi-exclamation-triangle', label: 'Fraud signals', badge: '' },
        { to: '/admin/broadcast', icon: 'pi pi-megaphone', label: 'Bulk notify', badge: '' },
      ],
    })
  }
  return sections
})

function isActive(path: string) {
  if (path === '/dashboard') return route.path === path
  return route.path === path || route.path.startsWith(path + '/')
}

function go(path: string) {
  router.push(path)
  ui.closeSidebar()
}

function logout() {
  auth.logout()
}
</script>

<template>
  <aside class="sidebar glass" :class="{ open: ui.sidebarOpen, collapsed: ui.sidebarCollapsed }">
    <div class="brand" @click="go('/dashboard')">
      <div class="mark">C</div>
      <div v-if="!ui.sidebarCollapsed" class="brand-text">
        <div class="name gradient-text">CryptoInvest</div>
        <div class="sub">Investment platform</div>
      </div>
    </div>

    <nav class="nav">
      <template v-for="section in nav" :key="section.label">
        <div v-if="!ui.sidebarCollapsed" class="section">{{ section.label }}</div>
        <button
          v-for="item in section.items"
          :key="item.to"
          type="button"
          class="link"
          :class="{ active: isActive(item.to), staff: section.label === 'Admin' }"
          :title="item.label"
          @click="go(item.to)"
        >
          <span class="ico-wrap">
            <i :class="item.icon" />
            <span v-if="item.badge && ui.sidebarCollapsed" class="nav-badge coll">{{ item.badge }}</span>
          </span>
          <span v-if="!ui.sidebarCollapsed" class="lbl">{{ item.label }}</span>
          <span v-if="item.badge && !ui.sidebarCollapsed" class="nav-badge">{{ item.badge }}</span>
        </button>
      </template>
    </nav>

    <div class="foot">
      <button type="button" class="link" @click="go('/search')">
        <i class="pi pi-search" />
        <span v-if="!ui.sidebarCollapsed">Search</span>
      </button>
      <button type="button" class="link" @click="logout">
        <i class="pi pi-sign-out" />
        <span v-if="!ui.sidebarCollapsed">Log out</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-w);
  position: fixed;
  top: 12px;
  left: 12px;
  bottom: 12px;
  z-index: 1040;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.25s ease, transform 0.25s ease;
}
.sidebar.collapsed { width: 76px; }
.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.15rem 1rem;
  border-bottom: 1px solid var(--ci-border);
  cursor: pointer;
  flex-shrink: 0;
}
.mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #3B82F6, #7C3AED);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
  flex-shrink: 0;
}
.brand-text .name { font-weight: 800; font-size: 1.05rem; }
.brand-text .sub {
  font-size: 0.62rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ci-muted);
  font-weight: 700;
}
.nav {
  flex: 1;
  overflow: auto;
  padding: 0.75rem 0.65rem;
}
.section {
  font-size: 0.62rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ci-muted);
  font-weight: 700;
  padding: 0.85rem 0.75rem 0.35rem;
}
.link {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.62rem 0.85rem;
  border-radius: 12px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--ci-muted);
  font-weight: 500;
  font-size: 0.88rem;
  cursor: pointer;
  margin-bottom: 2px;
  transition: 0.2s ease;
  text-align: left;
}
.link i { font-size: 1.05rem; width: 1.25rem; text-align: center; }
.ico-wrap { position: relative; display: inline-flex; }
.lbl { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nav-badge {
  min-width: 1.15rem;
  height: 1.15rem;
  padding: 0 0.32rem;
  border-radius: 999px;
  background: #25D366;
  color: #052e16;
  font-size: 0.65rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.nav-badge.coll {
  position: absolute;
  top: -6px;
  right: -8px;
  min-width: 0.95rem;
  height: 0.95rem;
  font-size: 0.55rem;
}
.link:hover { background: rgba(59, 130, 246, 0.1); color: var(--ci-text); }
.link.active {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.22), rgba(124, 58, 237, 0.08));
  border-color: rgba(96, 165, 250, 0.3);
  color: var(--ci-text);
  font-weight: 600;
}
.link.staff:not(.active) { color: #FBBF24; }
.foot {
  padding: 0.65rem;
  border-top: 1px solid var(--ci-border);
  flex-shrink: 0;
}
@media (max-width: 991.98px) {
  .sidebar {
    top: 0;
    left: 0;
    bottom: 0;
    border-radius: 0;
    transform: translateX(-105%);
    width: min(300px, 86vw);
    max-width: 320px;
    padding-top: env(safe-area-inset-top, 0px);
    padding-bottom: env(safe-area-inset-bottom, 0px);
    box-shadow: 12px 0 40px rgba(0, 0, 0, 0.35);
  }
  .sidebar.open { transform: translateX(0); }
  .sidebar.collapsed { width: min(300px, 86vw); }
  .link {
    padding: 0.72rem 0.9rem;
    min-height: 2.65rem;
    font-size: 0.9rem;
  }
  .nav { padding-bottom: 1rem; }
  .brand { padding: 1rem 0.9rem; }
}
</style>
