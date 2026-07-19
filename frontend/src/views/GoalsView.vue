<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import ProgressBar from 'primevue/progressbar'
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api } from '@/services/api'
import { formatMoney } from '@/utils/money'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const goals = ref<any[]>([])
const title = ref('')
const target = ref<number | null>(1000)
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const { data } = await api.goals()
    goals.value = data.results || []
  } finally {
    loading.value = false
  }
}

async function create() {
  if (!title.value.trim() || !target.value) return
  try {
    await api.createGoal({ title: title.value.trim(), target_amount: target.value })
    title.value = ''
    ui.toast('Goal created', 'Keep investing to hit your target', 'success')
    await load()
  } catch (e: any) {
    ui.toast('Failed', e?.response?.data?.detail || 'Could not create', 'error')
  }
}

async function remove(id: string) {
  await api.deleteGoal(id)
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="Savings goals" subtitle="Track how your investments move you toward a target" />
    <div class="glass form card">
      <label>Goal name <InputText v-model="title" class="w-full" placeholder="e.g. New laptop" /></label>
      <label>Target amount (USD)
        <InputNumber v-model="target" class="w-full" :min="1" mode="decimal" />
      </label>
      <Button label="Add goal" icon="pi pi-flag" @click="create" />
    </div>
    <div class="list">
      <div v-for="g in goals" :key="g.id" class="glass goal">
        <div class="top">
          <strong>{{ g.title }}</strong>
          <Button icon="pi pi-trash" text rounded severity="danger" @click="remove(g.id)" />
        </div>
        <p class="muted">{{ formatMoney(g.current_amount) }} / {{ formatMoney(g.target_amount) }}</p>
        <ProgressBar :value="g.progress_pct" />
        <span class="pct">{{ g.progress_pct }}%</span>
      </div>
      <EmptyState v-if="!loading && !goals.length" title="No goals yet" text="Set a target and grow toward it with investments." />
    </div>
  </div>
</template>

<style scoped>
.form { display: grid; gap: 0.75rem; padding: 1.1rem; margin-bottom: 1rem; border-radius: 16px; }
.form label { display: grid; gap: 0.3rem; font-size: 0.85rem; font-weight: 600; color: var(--ci-muted); }
.list { display: grid; gap: 0.75rem; }
.goal { padding: 1rem; border-radius: 16px; }
.top { display: flex; justify-content: space-between; align-items: center; }
.pct { font-size: 0.8rem; color: var(--ci-muted); }
</style>
