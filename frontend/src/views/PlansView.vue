<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Skeleton from 'primevue/skeleton'
import PageHeader from '@/components/ui/PageHeader.vue'
import PlanCard from '@/components/invest/PlanCard.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { api, unwrapList } from '@/services/api'
import type { InvestmentPlan } from '@/types/api'

const router = useRouter()
const loading = ref(true)
const plans = ref<InvestmentPlan[]>([])
const q = ref('')
const risk = ref<string | null>(null)

const risks = [
  { label: 'All risks', value: null },
  { label: 'Low', value: 'low' },
  { label: 'Medium', value: 'medium' },
  { label: 'High', value: 'high' },
]

const filtered = computed(() => {
  return plans.value.filter((p) => {
    const matchQ = !q.value || p.name.toLowerCase().includes(q.value.toLowerCase())
    const matchR = !risk.value || (p.risk_level || '').toLowerCase().includes(String(risk.value).toLowerCase())
    return matchQ && matchR
  })
})

onMounted(async () => {
  try {
    const { data } = await api.plans()
    plans.value = unwrapList(data)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="Investment plans" subtitle="Choose a plan that matches your strategy" />
    <div class="filters glass">
      <span class="p-input-icon-left grow">
        <i class="pi pi-search" />
        <InputText v-model="q" placeholder="Search plans…" class="w-full" />
      </span>
      <Select v-model="risk" :options="risks" option-label="label" option-value="value" placeholder="Risk" class="risk" />
    </div>

    <div v-if="loading" class="grid">
      <Skeleton v-for="i in 6" :key="i" height="280px" border-radius="18px" />
    </div>
    <div v-else-if="filtered.length" class="grid">
      <PlanCard
        v-for="p in filtered"
        :key="p.id"
        :plan="p"
        @invest="router.push(`/plans/${p.slug}`)"
      />
    </div>
    <div v-else class="glass">
      <EmptyState title="No plans found" text="Try another search or risk filter." />
    </div>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  padding: 0.85rem;
  margin-bottom: 1rem;
  align-items: center;
}
.grow { flex: 1 1 220px; position: relative; }
.grow i {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--ci-muted);
  z-index: 1;
}
.grow :deep(input) { padding-left: 2.25rem; width: 100%; }
.risk { min-width: 140px; }
.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}
@media (max-width: 1100px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) { .grid { grid-template-columns: 1fr; } }
.w-full { width: 100%; }
</style>
