<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import Badge from 'primevue/badge'
import Menu from 'primevue/menu'
import Select from 'primevue/select'
import type { MenuItem } from 'primevue/menuitem'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useUiStore } from '@/stores/ui'
import { useCurrencyStore } from '@/stores/currency'
import { api, unwrapList } from '@/services/api'
import { formatDisplay } from '@/utils/money'
import type { AppNotification } from '@/types/api'
import CryptoIcon from '@/components/ui/CryptoIcon.vue'

/** Always-visible sample icons (proves badges render even if a page has no crypto list). */
const tickerIcons = ['BTC', 'ETH', 'USDT', 'BNB', 'LTC']

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const theme = useThemeStore()
const ui = useUiStore()
const currency = useCurrencyStore()

const profileMenu = ref()
const notifMenu = ref()
const notifications = ref<AppNotification[]>([])

const title = computed(() => (route.meta.title as string) || 'Dashboard')
const available = computed(() =>
  formatDisplay(currency.balances?.available) || '—',
)
const unread = computed(() => notifications.value.filter((n) => !n.is_read).length)

const currencyModel = computed({
  get: () => currency.code,
  set: async (v: string) => {
    const ok = await currency.setCurrency(v)
    if (ok) ui.toast('Currency', `Display set to ${v}`, 'success')
    else if (currency.error) ui.toast('Currency', currency.error, 'error')
  },
})

const profileItems = computed<MenuItem[]>(() => {
  const items: MenuItem[] = [
    { label: auth.displayName, disabled: true },
    { separator: true },
    { label: 'Profile', icon: 'pi pi-user', command: () => router.push('/profile') },
    { label: 'Wallet', icon: 'pi pi-wallet', command: () => router.push('/wallet') },
    { label: 'Notifications', icon: 'pi pi-bell', command: () => router.push('/notifications') },
  ]
  if (auth.user?.is_staff_panel) {
    items.push(
      { separator: true },
      { label: 'Admin panel', icon: 'pi pi-cog', command: () => router.push('/admin') },
    )
  }
  items.push(
    { separator: true },
    {
      label: theme.mode === 'light' ? 'Dark mode' : 'Light mode',
      icon: theme.mode === 'light' ? 'pi pi-moon' : 'pi pi-sun',
      command: () => theme.toggleDarkLight(),
    },
    { label: 'Log out', icon: 'pi pi-sign-out', command: () => auth.logout() },
  )
  return items
})

const notifItems = computed<MenuItem[]>(() => {
  if (!notifications.value.length) {
    return [{ label: 'No notifications', disabled: true }]
  }
  return notifications.value.slice(0, 6).map((n) => ({
    label: n.title,
    icon: n.is_read ? 'pi pi-circle' : 'pi pi-circle-fill',
    command: async () => {
      if (!n.is_read) {
        try {
          await api.markNotificationRead(n.id)
          n.is_read = true
        } catch { /* ignore */ }
      }
      if (n.link) {
        if (n.link.startsWith('http')) window.location.href = n.link
        else router.push(n.link.startsWith('/') ? n.link.replace(/^\/app/, '') || '/' : `/${n.link}`)
      } else {
        router.push('/notifications')
      }
    },
  })).concat([
    { separator: true },
    { label: 'View all', icon: 'pi pi-arrow-right', command: () => router.push('/notifications') },
  ])
})

/** Opening the notification menu classifies them as viewed. */
async function openNotifMenu(e: Event) {
  notifMenu.value?.toggle(e)
  if (!unread.value) return
  try {
    await api.markAllNotificationsRead()
    notifications.value.forEach((n) => {
      n.is_read = true
    })
  } catch { /* ignore */ }
}

onMounted(async () => {
  try {
    await currency.init()
  } catch { /* ignore */ }
  try {
    const { data } = await api.notifications()
    notifications.value = unwrapList(data)
  } catch { /* ignore */ }
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
      <div class="crypto-ticker" title="Supported assets" @click="router.push('/wallet')">
        <CryptoIcon v-for="s in tickerIcons" :key="s" :symbol="s" size="sm" />
      </div>

      <div class="fx-wrap" v-tooltip.bottom="'Display currency · live conversion'">
        <Select
          v-model="currencyModel"
          :options="currency.options"
          option-label="label"
          option-value="code"
          placeholder="Currency"
          class="fx-select"
          :loading="currency.switching"
          :disabled="currency.switching"
        >
          <template #value="{ value }">
            <span v-if="value" class="fx-val">
              <CryptoIcon :symbol="value" size="xs" />
              <span>{{ value }}</span>
            </span>
            <span v-else>Currency</span>
          </template>
          <template #option="{ option }">
            <span class="fx-val">
              <CryptoIcon :symbol="option.code" size="xs" />
              <span>{{ option.label }}</span>
            </span>
          </template>
        </Select>
      </div>

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
          @click="openNotifMenu"
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
.crypto-ticker {
  display: none;
  align-items: center;
  gap: 0.28rem;
  padding: 0.2rem 0.4rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--ci-border);
  cursor: pointer;
}
@media (min-width: 900px) {
  .crypto-ticker { display: inline-flex; }
}
.fx-val {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
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
.fx-wrap { min-width: 0; }
.fx-select {
  min-width: 7.5rem;
  max-width: 11rem;
}
:deep(.fx-select .p-select) {
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 650;
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
  max-width: 14rem;
}
.balance .mono {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.balance:hover {
  border-color: rgba(59, 130, 246, 0.4);
}
.notif-wrap { position: relative; }
.badge {
  position: absolute;
  top: 2px;
  right: 2px;
}
.collapse-btn { display: none; }
.collapse-btn.rotated { transform: rotate(180deg); }
@media (min-width: 992px) {
  .menu-btn { display: none; }
  .collapse-btn { display: inline-flex; }
  .balance { display: inline-flex; }
}
@media (max-width: 991.98px) {
  .topbar {
    top: 0;
    border-radius: 0;
    margin-bottom: 0.5rem;
  }
  .sub { display: none; }
  .fx-select { min-width: 5.5rem; max-width: 7.5rem; }
}
</style>
