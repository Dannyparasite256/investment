<script setup lang="ts">
import { onMounted, ref } from 'vue'
import ProgressBar from 'primevue/progressbar'
import Skeleton from 'primevue/skeleton'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { formatMoney } from '@/utils/money'
import type { VipStatus } from '@/types/api'

const loading = ref(true)
const vip = ref<VipStatus | null>(null)

onMounted(async () => {
  try {
    const { data } = await api.vip()
    vip.value = data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="VIP status" subtitle="Loyalty tiers based on total invested" />
    <Skeleton v-if="loading" height="200px" border-radius="18px" />
    <template v-else-if="vip">
      <div class="hero glass">
        <div class="emoji">{{ vip.sticker_emoji || vip.tier?.sticker_emoji || '⭐' }}</div>
        <div>
          <div class="stat-label">Current tier</div>
          <h2 :style="{ color: vip.tier?.badge_color || undefined }">
            {{ vip.tier?.name || 'Starter' }}
          </h2>
          <p class="muted">Total invested · <span class="mono">{{ formatMoney(vip.total_invested) }}</span></p>
          <template v-if="vip.next_tier">
            <p class="muted small">
              {{ formatMoney(vip.remaining) }} more to reach <strong>{{ vip.next_tier.name }}</strong>
            </p>
            <ProgressBar :value="vip.progress_pct" class="mt" />
          </template>
          <p v-else class="success small">You are at the top tier.</p>
        </div>
      </div>

      <div class="tiers">
        <div
          v-for="t in vip.tiers"
          :key="t.id"
          class="glass tier"
          :class="{ current: vip.tier?.id === t.id }"
          :style="{ '--tier': t.badge_color }"
        >
          <div class="tier-emoji">{{ t.sticker_emoji || '🏅' }}</div>
          <h3>{{ t.name }}</h3>
          <p class="muted small">From {{ formatMoney(t.min_total_invested) }} invested</p>
          <ul>
            <li>Deposit fee {{ t.deposit_fee_percent }}%</li>
            <li>Withdraw fee {{ t.withdrawal_fee_percent }}%</li>
            <li>Referral boost +{{ t.referral_bonus_boost }}%</li>
          </ul>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.hero {
  display: flex;
  gap: 1.25rem;
  align-items: center;
  padding: 1.35rem;
  margin-bottom: 1rem;
}
.emoji { font-size: 3rem; line-height: 1; }
.tiers {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.85rem;
}
.tier {
  padding: 1rem;
  border-top: 3px solid var(--tier, #7C3AED);
}
.tier.current {
  box-shadow: 0 0 0 1px var(--tier), 0 12px 28px rgba(124, 58, 237, 0.2);
}
.tier-emoji { font-size: 1.5rem; }
.tier ul { margin: 0.5rem 0 0; padding-left: 1.1rem; color: var(--ci-muted); font-size: 0.85rem; }
.small { font-size: 0.85rem; }
.mt { margin-top: 0.5rem; }
.success { color: var(--ci-success); }
</style>
