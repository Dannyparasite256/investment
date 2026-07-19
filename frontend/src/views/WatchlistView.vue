<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import CryptoIcon from '@/components/ui/CryptoIcon.vue'
import { api } from '@/services/api'
import { useUiStore } from '@/stores/ui'
import type { WatchlistItem } from '@/types/api'

const ui = useUiStore()
const items = ref<WatchlistItem[]>([])
const symbol = ref('FX:EURUSD')
const label = ref('')
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const { data } = await api.watchlist()
    items.value = Array.isArray(data) ? data : []
  } finally {
    loading.value = false
  }
}

async function add() {
  if (!symbol.value.trim()) return
  try {
    await api.addWatchlist({ symbol: symbol.value.trim(), label: label.value.trim() })
    symbol.value = ''
    label.value = ''
    ui.toast('Added', 'Watchlist updated', 'success')
    await load()
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Could not add', 'error')
  }
}

async function remove(id: string) {
  await api.removeWatchlist(id)
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Watchlist" subtitle="Track symbols you care about" />
    <div class="glass card form">
      <InputText v-model="symbol" placeholder="Symbol e.g. FX:EURUSD" class="grow" />
      <InputText v-model="label" placeholder="Label (optional)" class="grow" />
      <Button label="Add" icon="pi pi-plus" @click="add" />
    </div>
    <div class="glass card">
      <EmptyState v-if="!loading && !items.length" title="Empty watchlist" text="Add FX or crypto symbols to track them here." />
      <ul v-else class="list">
        <li v-for="i in items" :key="i.id">
          <div>
            <strong class="mono sym-row">
              <CryptoIcon :symbol="i.symbol" size="sm" />
              {{ i.symbol }}
            </strong>
            <div class="muted small">{{ i.label || '—' }}</div>
          </div>
          <Button icon="pi pi-trash" text severity="danger" @click="remove(i.id)" />
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 1rem; margin-bottom: 0.85rem; }
.form { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.grow { flex: 1; min-width: 140px; }
.list { list-style: none; margin: 0; padding: 0; }
.list li {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.75rem 0; border-bottom: 1px solid var(--ci-border);
}
.list li:last-child { border-bottom: 0; }
.sym-row { display: inline-flex; align-items: center; gap: 0.45rem; }
.small { font-size: 0.8rem; }
</style>
