<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { useUiStore } from '@/stores/ui'

const router = useRouter()
const ui = useUiStore()
const steps = ref({
  has_deposit: false,
  has_investment: false,
  kyc_done: false,
  two_fa_done: false,
  tour_completed: false,
})

const checklist = computed(() => [
  { key: 'has_deposit', label: 'Make your first deposit', done: steps.value.has_deposit, to: '/deposits' },
  { key: 'has_investment', label: 'Start an investment plan', done: steps.value.has_investment, to: '/plans' },
  { key: 'kyc_done', label: 'Complete KYC verification', done: steps.value.kyc_done, to: '/kyc' },
  { key: 'two_fa_done', label: 'Enable two-factor authentication', done: steps.value.two_fa_done, to: '/security' },
])

const progress = computed(() => {
  const n = checklist.value.filter((c) => c.done).length
  return Math.round((n / checklist.value.length) * 100)
})

async function finish() {
  await api.completeTour()
  ui.toast('Welcome aboard', 'Onboarding complete', 'success')
  router.push('/dashboard')
}

onMounted(async () => {
  const { data } = await api.bootstrap()
  if (data.onboarding) steps.value = { ...steps.value, ...data.onboarding }
})
</script>

<template>
  <div>
    <PageHeader title="Get started" :subtitle="`${progress}% complete`" />
    <div class="glass card">
      <div v-for="s in checklist" :key="s.key" class="row" :class="{ done: s.done }">
        <i class="pi" :class="s.done ? 'pi-check-circle' : 'pi-circle'" />
        <span>{{ s.label }}</span>
        <Button v-if="!s.done" label="Go" size="small" text @click="router.push(s.to)" />
      </div>
      <Button class="mt" label="Mark tour complete" icon="pi pi-flag" @click="finish" />
    </div>
  </div>
</template>

<style scoped>
.card { padding: 1.1rem; border-radius: 16px; display: grid; gap: 0.65rem; }
.row { display: flex; align-items: center; gap: 0.65rem; padding: 0.55rem 0; border-bottom: 1px solid var(--ci-border); }
.row.done { color: var(--ci-success); }
.row .pi-check-circle { color: var(--ci-success); }
.mt { margin-top: 0.75rem; }
</style>
