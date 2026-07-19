<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api } from '@/services/api'
import { shortDate } from '@/utils/money'

const items = ref<any[]>([])
onMounted(async () => {
  const { data } = await api.announcements()
  items.value = data.results || []
})
</script>

<template>
  <div>
    <PageHeader title="Announcements" subtitle="News and platform updates" />
    <div class="list">
      <article v-for="a in items" :key="a.id" class="glass item">
        <div class="top">
          <strong>{{ a.title }}</strong>
          <Tag :value="a.level" />
        </div>
        <p>{{ a.message }}</p>
        <span class="muted small">{{ shortDate(a.created_at) }}</span>
      </article>
      <EmptyState v-if="!items.length" title="No announcements" text="Check back soon." />
    </div>
  </div>
</template>

<style scoped>
.list { display: grid; gap: 0.75rem; }
.item { padding: 1rem; border-radius: 16px; }
.top { display: flex; justify-content: space-between; gap: 0.5rem; margin-bottom: 0.4rem; }
.small { font-size: 0.8rem; }
</style>
