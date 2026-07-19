<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Tag from 'primevue/tag'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api } from '@/services/api'
import { shortDate } from '@/utils/money'
import type { TradingSignal } from '@/types/api'

const signals = ref<TradingSignal[]>([])
const disclaimer = ref('')
const loading = ref(true)

function sideSeverity(side: string) {
  if (side === 'buy') return 'success'
  if (side === 'sell') return 'danger'
  return 'info'
}

onMounted(async () => {
  try {
    const { data } = await api.signals()
    signals.value = data.results || []
    disclaimer.value = data.disclaimer || ''
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="Market signals" subtitle="Informational ideas from the platform team" />
    <EmptyState v-if="!loading && !signals.length" title="No signals" text="Published signals will appear here." />
    <div class="grid">
      <div v-for="s in signals" :key="s.id" class="glass card">
        <div class="top">
          <Tag :value="s.side.toUpperCase()" :severity="sideSeverity(s.side)" />
          <span class="muted small">{{ shortDate(s.created_at) }}</span>
        </div>
        <h3>{{ s.title }}</h3>
        <div class="mono symbol">{{ s.symbol }}</div>
        <p v-if="s.entry_note" class="muted">{{ s.entry_note }}</p>
        <div class="meta">
          <span v-if="s.target">Target <strong>{{ s.target }}</strong></span>
          <span v-if="s.stop_loss">SL <strong>{{ s.stop_loss }}</strong></span>
        </div>
      </div>
    </div>
    <p v-if="disclaimer" class="muted small disclaimer">{{ disclaimer }}</p>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 0.85rem; }
.card { padding: 1rem; }
.top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.symbol { margin: 0.25rem 0 0.5rem; color: #60A5FA; font-weight: 700; }
.meta { display: flex; gap: 1rem; font-size: 0.85rem; color: var(--ci-muted); }
.small { font-size: 0.8rem; }
.disclaimer { margin-top: 1rem; }
</style>
