<script setup lang="ts">
import type { InvestmentPlan } from '@/types/api'
import { formatMoney } from '@/utils/money'
import Button from 'primevue/button'
import Tag from 'primevue/tag'

defineProps<{ plan: InvestmentPlan }>()
defineEmits<{ invest: [] }>()
</script>

<template>
  <article class="plan glass" :class="{ featured: plan.is_featured }">
    <div v-if="plan.is_featured" class="ribbon">Popular</div>
    <div class="top">
      <h3>{{ plan.name }}</h3>
      <Tag :value="plan.risk_level || 'Balanced'" severity="info" rounded />
    </div>
    <div class="roi mono gradient-text">{{ plan.expected_return || `${plan.profit_rate_percent}%` }}</div>
    <p class="muted desc">{{ plan.short_description || plan.description }}</p>
    <ul class="meta">
      <li><span>Duration</span><strong>{{ plan.duration_days }} days</strong></li>
      <li><span>Min</span><strong class="mono">{{ formatMoney(plan.min_deposit) }}</strong></li>
      <li><span>Max</span><strong class="mono">{{ formatMoney(plan.max_deposit) }}</strong></li>
      <li><span>Payout</span><strong>{{ plan.payout_frequency }}</strong></li>
    </ul>
    <Button label="Invest now" icon="pi pi-arrow-right" icon-pos="right" class="w-full" @click="$emit('invest')" />
  </article>
</template>

<style scoped>
.plan {
  padding: 1.25rem;
  position: relative;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, border-color 0.2s ease;
}
.plan:hover {
  transform: translateY(-4px);
  border-color: rgba(59, 130, 246, 0.4);
}
.plan.featured {
  border-color: rgba(251, 191, 36, 0.35);
}
.ribbon {
  position: absolute;
  top: 0.85rem;
  right: 0.85rem;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.25), rgba(59, 130, 246, 0.15));
  color: #FDE68A;
  border: 1px solid rgba(251, 191, 36, 0.35);
}
.top {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}
h3 {
  font-size: 1.1rem;
  font-weight: 750;
}
.roi {
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  margin: 0.25rem 0 0.5rem;
}
.desc {
  font-size: 0.88rem;
  min-height: 2.6rem;
  margin: 0 0 0.85rem;
}
.meta {
  list-style: none;
  padding: 0;
  margin: 0 0 1rem;
  display: grid;
  gap: 0.4rem;
  flex: 1;
}
.meta li {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  padding: 0.4rem 0.55rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
}
.meta span { color: var(--ci-muted); }
.w-full { width: 100%; }
</style>
