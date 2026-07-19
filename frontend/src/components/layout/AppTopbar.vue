<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Menu from 'primevue/menu'
import type { MenuItem } from 'primevue/menuitem'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useUiStore } from '@/stores/ui'
import { api, unwrapList } from '@/services/api'
import { formatMoney } from '@/utils/money'
import type { AppNotification } from '@/types/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const theme = useThemeStore()
const ui = useUiStore()

const profileMenu = ref()
const notifMenu = ref()
const notifications = ref<AppNotification[]>([])

const title = computed(() => (route.meta.title as string) || 'Dashboard')
const available = computed(() => formatMoney(auth.wallet?.available_balance ?? 0, 2))
const unread = computed(() => notifications.value.filter((n) => !n.is_read).length)

const profileItems = computed<MenuItem[]>(() => [
  { label: auth.displayName, disabled: true },
  { separator: true },
  { label: 'Profile', icon: 'pi pi-user', command: () => router.push('/profile') },
  { label: 'Wallet', icon: 'pi pi-wallet', command: () => router.push('/wallet') },
  { label: 'Notifications', icon: 'pi pi-bell', command: () => router.push('/notifications') },
  { separator: true },
  {
    label: theme.mode === 'light' ? 'Dark mode' : 'Light mode',
    icon: theme.mode === 'light' ? 'pi pi-moon' : 'pi pi-sun',
    command: () => theme.toggleDarkLight(),
  },
  { label: 'Log out', icon: 'pi pi-sign-out', command: () => auth.logout() },
])

const notifItems = computed<MenuItem[]>(() => {
  if (!notifications.value.length) {
    return [{ label: 'No notifications', disabled: true }]
  }
  return notifications.value.slice(0, 6).map((n) => ({
    label: n.title,
    icon: n.is_read ? 'pi pi-circle' : 'pi pi-circle-fill',
    command: () => router.push('/notifications'),
  })).concat([
    { separator: true },
    { label: 'View all', icon: 'pi pi-arrow-right', command: () => router.push('/notifications') },
  ])
})

onMounted(async () => {
  try {
    const { data } = await api.notifications()
    notifications.value = unwrapList(data)
  } catch {
    /* ignore */
  }
})
</script>

<template>
  <header class="topbar glass">
    <div class="left">
      <Button
        icon="pi pi-bars"
        text
        rounded
        class="menu-btn"
        aria-label="Menu"
        @click="ui.toggleSidebar()"
      />
      <Button
        icon="pi pi-angle-double-left"
        text
        rounded
        class="collapse-btn"
        :class="{ rotated: ui.sidebarCollapsed }"
        aria-label="Collapse sidebar"
        @click="ui.toggleCollapse()"
      />
      <div class="titles">
        <div class="title">{{ title }}</div>
        <div class="sub muted">{{ auth.user?.email }}</div>
      </div>
    </div>

    <div class="right">
      <button type="button" class="balance" @click="router.push('/wallet')">
        <i class="pi pi-wallet" />
        <span class="mono">{{ available }}</span>
      </button>

      <Button
        :icon="theme.mode === 'light' ? 'pi pi-sun' : 'pi pi-moon'"
        text
        rounded
        aria-label="Toggle theme"
        @click="theme.toggleDarkLight()"
      />

      <div class="notif-wrap">
        <Button
          icon="pi pi-bell"
          text
          rounded
          aria-label="Notifications"
          @click="(e) => notifMenu.toggle(e)"
        />
        <Badge v-if="unread" :value="String(unread)" severity="danger" class="badge" />
        <Menu ref="notifMenu" :model="notifItems" popup />
      </div>

      <Button
        icon="pi pi-user"
        text
        rounded
        aria-label="Profile"
        @click="(e) => profileMenu.toggle(e)"
      />
      <Menu ref="profileMenu" :model="profileItems" popup />
    </div>
  </header>
</template>

<style scoped>
.topbar {
  min-height: var(--topbar-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.55rem 0.85rem;
  position: sticky;
  top: 12px;
  z-index: 20;
  margin-bottom: 1rem;
}
.left,
.right {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
}
.title {
  font-weight: 700;
  letter-spacing: -0.02em;
  font-size: 1.02rem;
}
.sub {
  font-size: 0.75rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}
.balance {
  display: none;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--ci-border);
  background: rgba(59, 130, 246, 0.1);
  color: var(--ci-text);
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
}
.balance:hover {
  border-color: rgba(59, 130, 246, 0.4);
}
.notif-wrap {
  position: relative;
}
.badge {
  position: absolute;
  top: 2px;
  right: 2px;
}
.collapse-btn {
  display: none;
}
.collapse-btn.rotated {
  transform: rotate(180deg);
}
@media (min-width: 992px) {
  .menu-btn { display: none; }
  .collapse-btn { display: inline-flex; }
  .balance { display: inline-flex; }
  .topbar { top: 12px; }
}
@media (max-width: 991.98px) {
  .topbar {
    top: 0;
    border-radius: 0;
    margin-bottom: 0.5rem;
  }
  .sub { display: none; }
}
</style>
