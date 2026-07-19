<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api, unwrapList } from '@/services/api'
import { shortDate } from '@/utils/money'
import { useUiStore } from '@/stores/ui'
import type { AppNotification } from '@/types/api'

const ui = useUiStore()
const rows = ref<AppNotification[]>([])
const loading = ref(true)
const filter = ref<'all' | 'unread'>('all')

const visible = computed(() =>
  filter.value === 'unread' ? rows.value.filter((n) => !n.is_read) : rows.value,
)
const unreadCount = computed(() => rows.value.filter((n) => !n.is_read).length)

const catIcon: Record<string, string> = {
  deposit: 'pi-download',
  withdrawal: 'pi-upload',
  investment: 'pi-chart-line',
  earning: 'pi-dollar',
  kyc: 'pi-id-card',
  security: 'pi-shield',
  referral: 'pi-users',
  announcement: 'pi-megaphone',
  system: 'pi-bell',
}

/** Opening the notifications page marks all as viewed. */
async function markAllViewed() {
  try {
    await api.markAllNotificationsRead()
    rows.value.forEach((n) => {
      n.is_read = true
    })
  } catch {
    /* ignore */
  }
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.notifications()
    rows.value = unwrapList(data)
    // Classify as viewed when the user opens this page
    if (rows.value.some((n) => !n.is_read)) {
      await markAllViewed()
    }
  } finally {
    loading.value = false
  }
}

async function openItem(n: AppNotification) {
  if (!n.is_read) {
    try {
      await api.markNotificationRead(n.id)
      n.is_read = true
    } catch {
      /* ignore */
    }
  }
  if (n.link) {
    if (n.link.startsWith('http')) window.location.href = n.link
    else window.location.assign(n.link.startsWith('/') ? n.link : `/${n.link}`)
  }
}

async function markAll() {
  try {
    await markAllViewed()
    ui.toast('Done', 'All notifications marked as viewed', 'success')
  } catch {
    ui.toast('Failed', 'Could not mark all read', 'error')
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Notifications" subtitle="Security, deposits, and account alerts">
      <Button
        label="Unread"
        size="small"
        :outlined="filter !== 'unread'"
        @click="filter = 'unread'"
      >
        <template v-if="unreadCount" #default>
          Unread ({{ unreadCount }})
        </template>
      </Button>
      <Button label="All" size="small" :outlined="filter !== 'all'" @click="filter = 'all'" />
      <Button
        v-if="unreadCount"
        label="Mark all viewed"
        icon="pi pi-check"
        size="small"
        outlined
        @click="markAll"
      />
    </PageHeader>

    <div class="glass list">
      <button
        v-for="n in visible"
        :key="n.id"
        type="button"
        class="item"
        :class="{ unread: !n.is_read, [`level-${n.level}`]: true }"
        @click="openItem(n)"
      >
        <span class="icon" :class="`cat-${n.category || 'system'}`">
          <i class="pi" :class="catIcon[n.category] || 'pi-bell'" />
        </span>
        <div class="body">
          <div class="top">
            <strong>{{ n.title }}</strong>
            <span v-if="!n.is_read" class="pill">New</span>
            <span class="muted small">{{ shortDate(n.created_at) }}</span>
          </div>
          <p class="muted">{{ n.message }}</p>
        </div>
        <span v-if="!n.is_read" class="dot" />
      </button>
      <EmptyState v-if="!loading && !visible.length" title="All caught up" text="No notifications in this view." />
    </div>
  </div>
</template>

<style scoped>
.list { padding: 0.25rem; overflow: hidden; }
.item {
  width: 100%;
  display: flex;
  gap: 0.85rem;
  align-items: flex-start;
  text-align: left;
  padding: 0.95rem 1rem;
  border: 0;
  border-bottom: 1px solid var(--ci-border);
  background: transparent;
  color: inherit;
  cursor: pointer;
  position: relative;
}
.item:hover { background: rgba(59, 130, 246, 0.07); }
.item.unread {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.1), transparent 60%);
}
.icon {
  width: 40px; height: 40px; border-radius: 12px;
  display: grid; place-items: center; flex-shrink: 0;
  background: rgba(255,255,255,0.06); border: 1px solid var(--ci-border);
}
.cat-deposit { color: #34D399; }
.cat-withdrawal { color: #60A5FA; }
.cat-investment { color: #A78BFA; }
.cat-security { color: #F87171; }
.body { flex: 1; min-width: 0; }
.top {
  display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; margin-bottom: 0.2rem;
}
.pill {
  font-size: 0.65rem; font-weight: 800; text-transform: uppercase;
  padding: 0.1rem 0.4rem; border-radius: 999px;
  background: rgba(239, 68, 68, 0.15); color: #F87171;
}
p { margin: 0; font-size: 0.9rem; }
.small { font-size: 0.78rem; margin-left: auto; white-space: nowrap; }
.dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #EF4444; margin-top: 0.4rem; flex-shrink: 0;
}
</style>
