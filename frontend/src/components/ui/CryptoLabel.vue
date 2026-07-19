<script setup lang="ts">
import CryptoIcon from '@/components/ui/CryptoIcon.vue'

withDefaults(
  defineProps<{
    symbol?: string | null
    icon?: string | null
    name?: string | null
    network?: string | null
    size?: 'xs' | 'sm' | 'md' | 'lg'
    /** Show network / secondary text */
    showNetwork?: boolean
  }>(),
  {
    size: 'sm',
    showNetwork: false,
  },
)
</script>

<template>
  <span class="crypto-label" :class="`sz-${size}`">
    <CryptoIcon :symbol="symbol" :icon="icon" :name="name" :size="size" />
    <span class="meta">
      <span class="sym">{{ symbol || '—' }}</span>
      <span v-if="showNetwork && network" class="net muted">{{ network }}</span>
      <span v-else-if="name && name !== symbol" class="net muted">{{ name }}</span>
    </span>
  </span>
</template>

<style scoped>
.crypto-label {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  min-width: 0;
  max-width: 100%;
  vertical-align: middle;
}
.meta {
  display: inline-flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.15;
}
.sym {
  font-weight: 700;
  font-size: 0.9em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.net {
  font-size: 0.72em;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sz-xs .sym { font-size: 0.8em; }
.sz-lg .sym { font-size: 1em; }
.muted { color: var(--ci-muted, #94a3b8); }
</style>
