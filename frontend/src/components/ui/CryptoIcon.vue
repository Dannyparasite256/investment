<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { cryptoColor, cryptoGlyph, cryptoIconUrl } from '@/utils/cryptoIcons'

const props = withDefaults(
  defineProps<{
    symbol?: string | null
    /** Emoji / glyph from API `icon` field */
    icon?: string | null
    name?: string | null
    size?: 'sm' | 'md' | 'lg'
    /** Prefer CDN image; falls back to glyph badge if load fails */
    image?: boolean
  }>(),
  {
    size: 'md',
    image: true,
  },
)

const imgFailed = ref(false)
const src = computed(() => cryptoIconUrl(props.symbol))
const glyph = computed(() => cryptoGlyph(props.symbol, props.icon))
const color = computed(() => cryptoColor(props.symbol))
const title = computed(() => props.name || props.symbol || 'Crypto')
const showImg = computed(() => props.image && !imgFailed.value)

watch(
  () => props.symbol,
  () => {
    imgFailed.value = false
  },
)
</script>

<template>
  <span
    class="crypto-icon"
    :class="[`sz-${size}`, { glyph: !showImg }]"
    :style="!showImg ? { background: color } : undefined"
    :title="title"
    role="img"
    :aria-label="title"
  >
    <img
      v-if="showImg"
      :src="src"
      :alt="title"
      class="crypto-img"
      loading="lazy"
      @error="imgFailed = true"
    />
    <span v-else class="crypto-glyph">{{ glyph }}</span>
  </span>
</template>

<style scoped>
.crypto-icon {
  display: inline-grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  vertical-align: middle;
  line-height: 1;
}
.crypto-icon.glyph {
  color: #fff;
  font-weight: 800;
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}
.sz-sm { width: 1.35rem; height: 1.35rem; font-size: 0.72rem; }
.sz-md { width: 1.75rem; height: 1.75rem; font-size: 0.9rem; }
.sz-lg { width: 2.4rem; height: 2.4rem; font-size: 1.15rem; }
.crypto-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.crypto-glyph {
  display: block;
  transform: translateY(0.5px);
}
</style>
