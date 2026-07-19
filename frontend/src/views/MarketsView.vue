<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import CryptoIcon from '@/components/ui/CryptoIcon.vue'
import { api } from '@/services/api'

const prices = ref<Record<string, string | number>>({})
const source = ref('')
const loading = ref(true)
let timer: number | undefined

async function load() {
  try {
    const { data } = await api.prices()
    prices.value = data.prices || {}
    source.value = data.source || ''
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  load()
  timer = window.setInterval(load, 60000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div>
    <PageHeader title="Markets" :subtitle="source ? `Live via ${source}` : 'Live market overview'" />
    <div class="grid">
      <div v-for="(v, k) in prices" :key="k" class="glass card">
        <div class="sym">
          <CryptoIcon :symbol="String(k)" size="md" />
          <span>{{ k }}</span>
        </div>
        <div class="price mono gradient-text">${{ v }}</div>
        <div class="muted small">USD</div>
      </div>
      <div v-if="!Object.keys(prices).length && !loading" class="glass empty muted">
        Price feed unavailable right now.
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
}
@media (max-width: 900px) { .grid { grid-template-columns: repeat(2, 1fr); gap: 0.55rem; } }
@media (max-width: 480px) {
  .grid { grid-template-columns: 1fr 1fr; gap: 0.5rem; }
  .card { padding: 0.85rem 0.7rem; }
  .price { font-size: 1.15rem; }
}
@media (max-width: 360px) {
  .grid { grid-template-columns: 1fr; }
}
.card { padding: 1.15rem; }
.sym {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--ci-muted);
  font-size: 0.85rem;
}
.price { font-size: 1.55rem; font-weight: 800; margin: 0.35rem 0 0.15rem; }
.small { font-size: 0.78rem; }
.empty { padding: 2rem; text-align: center; grid-column: 1 / -1; }
</style>
