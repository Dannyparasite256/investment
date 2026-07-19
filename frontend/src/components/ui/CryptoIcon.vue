<script setup lang="ts">
import { computed } from 'vue'
import { cryptoColor, cryptoGlyph, cryptoSizePx } from '@/utils/cryptoIcons'

const props = withDefaults(
  defineProps<{
    symbol?: string | null
    icon?: string | null
    name?: string | null
    size?: 'xs' | 'sm' | 'md' | 'lg'
  }>(),
  { size: 'md' },
)

const letter = computed(() => cryptoGlyph(props.symbol, props.icon) || '?')
const color = computed(() => cryptoColor(props.symbol) || '#64748B')
const title = computed(() => props.name || props.symbol || 'Crypto')
const px = computed(() => cryptoSizePx(props.size))
const fontPx = computed(() => Math.max(11, Math.round(px.value * 0.5)))

/** Style as a plain string — most reliable across PrimeVue portals / tables */
const styleAttr = computed(
  () =>
    `display:inline-flex !important;align-items:center;justify-content:center;` +
    `flex-shrink:0;width:${px.value}px;height:${px.value}px;` +
    `min-width:${px.value}px;min-height:${px.value}px;` +
    `border-radius:50%;background:${color.value};color:#fff;` +
    `font-weight:800;font-size:${fontPx.value}px;line-height:1;` +
    `font-family:Inter,system-ui,sans-serif;` +
    `box-shadow:0 2px 8px rgba(0,0,0,.4);border:2px solid rgba(255,255,255,.3);` +
    `vertical-align:middle;box-sizing:border-box;user-select:none;`,
)
</script>

<template>
  <span
    class="ci-crypto-icon"
    :style="styleAttr"
    :title="title"
    role="img"
    :aria-label="title"
  >{{ letter }}</span>
</template>
