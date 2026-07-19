<script setup lang="ts">
import CryptoIcon from '@/components/ui/CryptoIcon.vue'

withDefaults(
  defineProps<{
    symbol?: string | null
    icon?: string | null
    name?: string | null
    network?: string | null
    size?: 'xs' | 'sm' | 'md' | 'lg'
    showNetwork?: boolean
  }>(),
  {
    size: 'sm',
    showNetwork: false,
  },
)
</script>

<template>
  <span
    class="ci-crypto-label"
    style="display:inline-flex;align-items:center;gap:8px;min-width:0;max-width:100%;vertical-align:middle"
  >
    <CryptoIcon :symbol="symbol" :icon="icon" :name="name" :size="size" />
    <span style="display:inline-flex;flex-direction:column;min-width:0;line-height:1.2">
      <span style="font-weight:700;font-size:0.92em;white-space:nowrap">{{ symbol || '—' }}</span>
      <span
        v-if="showNetwork && network"
        style="font-size:0.72em;opacity:0.7;white-space:nowrap"
      >{{ network }}</span>
      <span
        v-else-if="name && name !== symbol"
        style="font-size:0.72em;opacity:0.7;white-space:nowrap"
      >{{ name }}</span>
    </span>
  </span>
</template>
