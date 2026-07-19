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

const letter = computed(() => cryptoGlyph(props.symbol, props.icon))
const color = computed(() => cryptoColor(props.symbol))
const title = computed(() => props.name || props.symbol || 'Crypto')
const px = computed(() => cryptoSizePx(props.size))
const fontPx = computed(() => Math.max(10, Math.round(px.value * 0.48)))

/** Fully inline styles so no global CSS can hide the badge */
const boxStyle = computed(() => ({
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  flexShrink: '0',
  width: `${px.value}px`,
  height: `${px.value}px`,
  minWidth: `${px.value}px`,
  minHeight: `${px.value}px`,
  borderRadius: '50%',
  backgroundColor: color.value,
  color: '#ffffff',
  fontWeight: '800',
  fontSize: `${fontPx.value}px`,
  lineHeight: '1',
  fontFamily: 'Inter, system-ui, -apple-system, Segoe UI, sans-serif',
  boxShadow: '0 2px 6px rgba(0,0,0,0.35)',
  border: '2px solid rgba(255,255,255,0.25)',
  verticalAlign: 'middle',
  boxSizing: 'border-box' as const,
  userSelect: 'none' as const,
}))
</script>

<template>
  <span
    class="ci-crypto-icon"
    :style="boxStyle"
    :title="title"
    role="img"
    :aria-label="title"
  >{{ letter }}</span>
</template>
