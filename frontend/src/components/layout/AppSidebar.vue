<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const ui = useUiStore()

const nav = [
  {
    label: 'Main',
    items: [
      { to: '/dashboard', icon: 'pi pi-th-large', label: 'Dashboard' },
      { to: '/plans', icon: 'pi pi-chart-line', label: 'Invest' },
      { to: '/investments', icon: 'pi pi-briefcase', label: 'Portfolio' },
      { to: '/markets', icon: 'pi pi-chart-bar', label: 'Markets' },
    ],
  },
  {
    label: 'Wallet',
    items: [
      { to: '/wallet', icon: 'pi pi-wallet', label: 'Wallet' },
      { to: '/deposits', icon: 'pi pi-download', label: 'Deposit' },
      { to: '/withdrawals', icon: 'pi pi-upload', label: 'Withdraw' },
      { to: '/transactions', icon: 'pi pi-history', label: 'History' },
      { to: '/earnings', icon: 'pi pi-dollar', label: 'Earnings' },
    ],
  },
  {
    label: 'Account',
    items: [
      { to: '/referrals', icon: 'pi pi-users', label: 'Referrals' },
      { to: '/notifications', icon: 'pi pi-bell', label: 'Notifications' },
      { to: '/profile', icon: 'pi pi-user', label: 'Profile' },
    ],
  },
]

function isActive(path: string) {
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
          :class="{ active: isActive(item.to) }"
          :title="item.label"
          @click="go(item.to)"
        >
          <i :class="item.icon" />
          <span v-if="!ui.sidebarCollapsed">{{ item.label }}</span>
        </button>
      </template>
    </nav>

    <div class="foot">
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
.sidebar.collapsed {
  width: 76px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.15rem 1rem;
  border-bottom: 1px solid var(--ci-border);
  cursor: pointer;
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
.brand-text .name {
  font-weight: 800;
  font-size: 1.05rem;
}
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
  padding: 0.7rem 0.85rem;
  border-radius: 12px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--ci-muted);
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  margin-bottom: 2px;
  transition: 0.2s ease;
  text-align: left;
}
.link i {
  font-size: 1.05rem;
  width: 1.25rem;
  text-align: center;
}
.link:hover {
  background: rgba(59, 130, 246, 0.1);
  color: var(--ci-text);
}
.link.active {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.22), rgba(124, 58, 237, 0.08));
  border-color: rgba(96, 165, 250, 0.3);
  color: var(--ci-text);
  font-weight: 600;
}
.foot {
  padding: 0.75rem;
  border-top: 1px solid var(--ci-border);
}
@media (max-width: 991.98px) {
  .sidebar {
    top: 0;
    left: 0;
    bottom: 0;
    border-radius: 0;
    transform: translateX(-105%);
    width: min(280px, 88vw);
  }
  .sidebar.open {
    transform: translateX(0);
  }
  .sidebar.collapsed {
    width: min(280px, 88vw);
  }
}
</style>
