<script setup lang="ts">
import { computed } from 'vue'
import { cryptoColor, cryptoGlyph, cryptoIconUrl } from '@/utils/cryptoIcons'

const props = withDefaults(
  defineProps<{
    symbol?: string | null
    /** Emoji / glyph from API `icon` field */
    icon?: string | null
    name?: string | null
    size?: 'xs' | 'sm' | 'md' | 'lg'
  }>(),
  {
    size: 'md',
  },
)

const src = computed(() => cryptoIconUrl(props.symbol, props.icon))
const glyph = computed(() => cryptoGlyph(props.symbol, props.icon))
const color = computed(() => cryptoColor(props.symbol))
const title = computed(() => props.name || props.symbol || 'Crypto')
</script>

<template>
  <span
    class="crypto-icon"
    :class="`sz-${size}`"
    :style="{ background: color }"
    :title="title"
    role="img"
    :aria-label="title"
  >
    <!-- Always use offline data-URI SVG; img is preferred for crisp glyphs -->
    <img :src="src" :alt="title" class="crypto-img" draggable="false" />
    <span class="crypto-glyph sr-only">{{ glyph }}</span>
  </span>
</template>

<style scoped>
.crypto-icon {
  display: inline-grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
  vertical-align: middle;
  line-height: 1;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.28);
  border: 1.5px solid rgba(255, 255, 255, 0.18);
}
.sz-xs { width: 1.1rem; height: 1.1rem; }
.sz-sm { width: 1.4rem; height: 1.4rem; }
.sz-md { width: 1.85rem; height: 1.85rem; }
.sz-lg { width: 2.5rem; height: 2.5rem; }
.crypto-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
