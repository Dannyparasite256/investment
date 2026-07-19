<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api, unwrapList } from '@/services/api'
import { shortDate } from '@/utils/money'
import type { AppNotification } from '@/types/api'

const rows = ref<AppNotification[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.notifications()
    rows.value = unwrapList(data)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="Notifications" subtitle="Security, deposits, and account alerts" />
    <div class="glass list">
      <div v-for="n in rows" :key="n.id" class="item" :class="{ unread: !n.is_read }">
        <div class="top">
          <strong>{{ n.title }}</strong>
          <span class="muted small">{{ shortDate(n.created_at) }}</span>
        </div>
        <p class="muted">{{ n.message }}</p>
      </div>
      <EmptyState v-if="!loading && !rows.length" title="All caught up" text="No notifications yet." />
    </div>
  </div>
</template>

<style scoped>
.list { padding: 0.35rem; }
.item {
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--ci-border);
}
.item.unread {
  border-left: 3px solid #3B82F6;
  background: rgba(59, 130, 246, 0.06);
}
.top {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}
p { margin: 0; font-size: 0.9rem; }
.small { font-size: 0.78rem; white-space: nowrap; }
</style>
