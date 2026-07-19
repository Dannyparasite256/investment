<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { cryptoColor, cryptoGlyph, cryptoLogoUrl, cryptoSizePx } from '@/utils/cryptoIcons'

const props = withDefaults(
  defineProps<{
    symbol?: string | null
    icon?: string | null
    name?: string | null
    size?: 'xs' | 'sm' | 'md' | 'lg'
  }>(),
  { size: 'md' },
)

const imgFailed = ref(false)
const letter = computed(() => cryptoGlyph(props.symbol, props.icon) || '?')
const color = computed(() => cryptoColor(props.symbol) || '#64748B')
const title = computed(() => props.name || props.symbol || 'Crypto')
const px = computed(() => cryptoSizePx(props.size))
const fontPx = computed(() => Math.max(11, Math.round(px.value * 0.5)))
const logoSrc = computed(() => cryptoLogoUrl(props.symbol))
const showImg = computed(() => !!logoSrc.value && !imgFailed.value)

watch(
  () => props.symbol,
  () => {
    imgFailed.value = false
  },
)

const boxStyle = computed(() => {
  const base =
    `display:inline-flex !important;align-items:center;justify-content:center;` +
    `flex-shrink:0;width:${px.value}px;height:${px.value}px;` +
    `min-width:${px.value}px;min-height:${px.value}px;` +
    `border-radius:50%;overflow:hidden;vertical-align:middle;` +
    `box-sizing:border-box;user-select:none;` +
    `box-shadow:0 2px 8px rgba(0,0,0,.35);border:1.5px solid rgba(255,255,255,.22);`
  if (showImg.value) {
    return base + `background:#fff;`
  }
  return (
    base +
    `background:${color.value};color:#fff;font-weight:800;font-size:${fontPx.value}px;` +
    `line-height:1;font-family:Inter,system-ui,sans-serif;`
  )
})
</script>

<template>
  <span
    class="ci-crypto-icon"
    :style="boxStyle"
    :title="title"
    role="img"
    :aria-label="title"
  >
    <img
      v-if="showImg && logoSrc"
      :src="logoSrc"
      :alt="title"
      style="width:100%;height:100%;object-fit:cover;display:block"
      draggable="false"
      @error="imgFailed = true"
    />
    <template v-else>{{ letter }}</template>
  </span>
</template>
