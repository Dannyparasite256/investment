<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import type { SearchResult } from '@/types/api'

const router = useRouter()
const q = ref('')
const results = ref<SearchResult[]>([])
const loading = ref(false)
let timer: number | undefined

watch(q, (val) => {
  window.clearTimeout(timer)
  if (val.trim().length < 2) {
    results.value = []
    return
  }
  timer = window.setTimeout(async () => {
    loading.value = true
    try {
      const { data } = await api.search(val.trim())
      results.value = data.results || []
    } finally {
      loading.value = false
    }
  }, 250)
})

function go(path: string) {
  router.push(path)
}
</script>

<template>
  <div>
    <PageHeader title="Search" subtitle="Find deposits, investments, tickets, and pages" />
    <div class="glass card">
      <span class="p-input-icon-left w-full">
        <i class="pi pi-search" />
        <InputText v-model="q" class="w-full" placeholder="Type at least 2 characters…" autofocus />
      </span>
      <p v-if="loading" class="muted small">Searching…</p>
      <ul class="results">
        <li v-for="(r, i) in results" :key="i" @click="go(r.path)">
          <div class="type">{{ r.type }}</div>
          <div>
            <div class="title">{{ r.title }}</div>
            <div class="muted small">{{ r.subtitle }}</div>
          </div>
          <i class="pi pi-chevron-right muted" />
        </li>
      </ul>
      <p v-if="q.length >= 2 && !loading && !results.length" class="muted">No matches.</p>
    </div>
  </div>
</template>

<style scoped>
.card { padding: 1rem; max-width: 720px; }
.results { list-style: none; margin: 0.85rem 0 0; padding: 0; }
.results li {
  display: grid;
  grid-template-columns: 72px 1fr auto;
  gap: 0.75rem;
  align-items: center;
  padding: 0.75rem;
  border-radius: 12px;
  cursor: pointer;
  border: 1px solid transparent;
}
.results li:hover { background: rgba(59, 130, 246, 0.08); border-color: var(--ci-border); }
.type {
  font-size: 0.68rem;
  font-weight: 750;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #60A5FA;
}
.title { font-weight: 700; }
.small { font-size: 0.82rem; }
</style>
