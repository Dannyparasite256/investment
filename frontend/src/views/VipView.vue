<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import ProgressBar from 'primevue/progressbar'
import Skeleton from 'primevue/skeleton'
import PageHeader from '@/components/ui/PageHeader.vue'
import { api } from '@/services/api'
import { formatMoney } from '@/utils/money'
import { useAuthStore } from '@/stores/auth'
import type { VipStatus } from '@/types/api'

const auth = useAuthStore()
const loading = ref(true)
const vip = ref<VipStatus | null>(null)

const memberName = computed(
  () => vip.value?.member?.name || auth.displayName || auth.user?.email || 'Member',
)
const avatarUrl = computed(
  () => vip.value?.member?.avatar_url || auth.user?.avatar_url || '',
)
const initials = computed(() => {
  if (vip.value?.member?.initials) return vip.value.member.initials
  const n = memberName.value.trim()
  const parts = n.split(/\s+/).filter(Boolean)
  if (!parts.length) return 'U'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
})
const tierColor = computed(() => vip.value?.tier?.badge_color || '#7C3AED')

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
    <PageHeader title="VIP Lounge" subtitle="Your profile · loyalty tiers · fee boosts" />
    <Skeleton v-if="loading" height="220px" border-radius="18px" />
    <template v-else-if="vip">
      <div class="hero glass" :style="{ '--tier': tierColor }">
        <div class="member-col">
          <div class="photo-wrap">
            <img
              v-if="avatarUrl"
              :src="avatarUrl"
              :alt="memberName"
              class="photo"
              referrerpolicy="no-referrer"
            />
            <span v-else class="photo fallback">{{ initials }}</span>
            <span class="ring" aria-hidden="true" />
            <span class="tier-chip" :title="vip.tier?.name || 'Starter'">
              {{ vip.sticker_emoji || vip.tier?.sticker_emoji || '⭐' }}
            </span>
          </div>
          <div class="member-name">{{ memberName }}</div>
          <div class="muted tiny">VIP Lounge member</div>
        </div>

        <div class="hero-copy">
          <div class="stat-label">Current tier</div>
          <h2 :style="{ color: vip.tier?.badge_color || undefined }">
            {{ vip.sticker_emoji || vip.tier?.sticker_emoji || '⭐' }}
            {{ vip.tier?.name || 'Starter' }}
          </h2>
          <p class="muted">
            Total invested · <span class="mono">{{ formatMoney(vip.total_invested) }}</span>
          </p>
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
          <div v-if="vip.tier?.id === t.id" class="card-photo">
            <img
              v-if="avatarUrl"
              :src="avatarUrl"
              :alt="memberName"
              referrerpolicy="no-referrer"
            />
            <span v-else class="card-fallback">{{ initials.slice(0, 1) }}</span>
          </div>
          <div class="tier-emoji">{{ t.sticker_emoji || '🏅' }}</div>
          <h3>{{ t.name }}</h3>
          <p class="muted small">From {{ formatMoney(t.min_total_invested) }} invested</p>
          <ul>
            <li>Deposit fee {{ t.deposit_fee_percent }}%</li>
            <li>Withdraw fee {{ t.withdrawal_fee_percent }}%</li>
            <li>Referral boost +{{ t.referral_bonus_boost }}%</li>
          </ul>
          <span v-if="vip.tier?.id === t.id" class="you">You</span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.hero {
  display: flex;
  gap: 1.5rem;
  align-items: center;
  padding: 1.4rem 1.5rem;
  margin-bottom: 1rem;
  position: relative;
  overflow: hidden;
}
.hero::before {
  content: '';
  position: absolute;
  inset: -40% -15% auto auto;
  width: 240px;
  height: 240px;
  background: radial-gradient(circle, color-mix(in srgb, var(--tier, #7C3AED) 40%, transparent), transparent 70%);
  pointer-events: none;
}
.member-col {
  text-align: center;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}
.photo-wrap {
  position: relative;
  width: 112px;
  height: 112px;
  margin: 0 auto 0.55rem;
}
.photo,
.fallback {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  display: block;
  border: 3px solid color-mix(in srgb, var(--tier, #7C3AED) 75%, #fff);
  box-shadow:
    0 0 0 4px color-mix(in srgb, var(--tier, #7C3AED) 28%, transparent),
    0 12px 28px rgba(0, 0, 0, 0.3);
  background: linear-gradient(145deg, rgba(124, 58, 237, 0.4), rgba(15, 23, 42, 0.9));
}
.fallback {
  display: grid;
  place-items: center;
  font-size: 2.2rem;
  font-weight: 800;
  color: #fff;
}
.ring {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 2px dashed color-mix(in srgb, var(--tier, #7C3AED) 55%, transparent);
  animation: spin 8s linear infinite;
  pointer-events: none;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.tier-chip {
  position: absolute;
  right: -2px;
  bottom: 0;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 1rem;
  background: rgba(15, 23, 42, 0.92);
  border: 2px solid color-mix(in srgb, var(--tier, #7C3AED) 65%, #fff);
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.3);
}
.member-name {
  font-weight: 750;
  font-size: 0.98rem;
  max-width: 140px;
  margin: 0 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tiny { font-size: 0.75rem; }
.hero-copy { min-width: 0; position: relative; z-index: 1; flex: 1; }
.hero-copy h2 {
  margin: 0.15rem 0 0.35rem;
  font-size: 1.65rem;
  letter-spacing: -0.02em;
}
.tiers {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.85rem;
}
.tier {
  padding: 1rem;
  border-top: 3px solid var(--tier, #7C3AED);
  position: relative;
  text-align: center;
}
.tier.current {
  box-shadow: 0 0 0 1px var(--tier), 0 12px 28px rgba(124, 58, 237, 0.2);
}
.card-photo {
  width: 52px;
  height: 52px;
  margin: 0 auto 0.45rem;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid color-mix(in srgb, var(--tier, #7C3AED) 70%, #fff);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--tier, #7C3AED) 22%, transparent);
}
.card-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.card-fallback {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(145deg, rgba(124, 58, 237, 0.45), rgba(15, 23, 42, 0.9));
}
.tier-emoji { font-size: 1.5rem; }
.tier h3 { margin: 0.25rem 0 0.15rem; font-size: 1.05rem; }
.tier ul {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
  color: var(--ci-muted);
  font-size: 0.85rem;
  text-align: left;
}
.you {
  position: absolute;
  top: 0.65rem;
  right: 0.65rem;
  font-size: 0.68rem;
  font-weight: 800;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--tier) 22%, transparent);
  color: var(--tier);
  border: 1px solid color-mix(in srgb, var(--tier) 45%, transparent);
}
.small { font-size: 0.85rem; }
.mt { margin-top: 0.5rem; }
.success { color: var(--ci-success); }

@media (max-width: 575.98px) {
  .hero {
    flex-direction: column;
    text-align: center;
  }
  .hero-copy { width: 100%; }
}
</style>
