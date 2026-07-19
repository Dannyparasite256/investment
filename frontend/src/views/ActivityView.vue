<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api, unwrapList } from '@/services/api'
import { shortDate } from '@/utils/money'
import type { ActivityEvent } from '@/types/api'

const events = ref<ActivityEvent[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.activity()
    events.value = unwrapList(data as any)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="Activity" subtitle="Timeline of account events" />
    <div class="glass card">
      <EmptyState v-if="!loading && !events.length" title="No activity yet" text="Logins, deposits, and investments will show up here." />
      <ul v-else class="timeline">
        <li v-for="e in events" :key="e.id">
          <div class="dot" />
          <div>
            <div class="title">{{ e.title }}</div>
            <div class="muted small">{{ e.event_type }} · {{ shortDate(e.created_at) }}</div>
            <p v-if="e.description" class="desc">{{ e.description }}</p>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 1.15rem; }
.timeline { list-style: none; margin: 0; padding: 0; }
.timeline li {
  display: grid;
  grid-template-columns: 16px 1fr;
  gap: 0.75rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--ci-border);
  position: relative;
}
.dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: linear-gradient(135deg, #3B82F6, #7C3AED);
  margin-top: 0.35rem;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.15);
}
.title { font-weight: 700; }
.desc { margin: 0.35rem 0 0; color: var(--ci-muted); font-size: 0.9rem; }
.small { font-size: 0.8rem; }
</style>
