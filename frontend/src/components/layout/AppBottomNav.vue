<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
const route = useRoute()
const router = useRouter()
const items = [
  { to: '/dashboard', icon: 'pi pi-th-large', label: 'Home' },
  { to: '/plans', icon: 'pi pi-chart-line', label: 'Invest' },
  { to: '/deposits', icon: 'pi pi-download', label: 'Deposit', fab: true },
  { to: '/wallet', icon: 'pi pi-wallet', label: 'Wallet' },
  { to: '/profile', icon: 'pi pi-user', label: 'More' },
]
function active(to: string) {
  return route.path === to || route.path.startsWith(to + '/')
}
</script>

<template>
  <nav class="bottom glass" aria-label="Primary">
    <button
      v-for="item in items"
      :key="item.to"
      type="button"
      class="item"
      :class="{ active: active(item.to), fab: item.fab }"
      @click="router.push(item.to)"
    >
      <span v-if="item.fab" class="fab-circle"><i :class="item.icon" /></span>
      <i v-else :class="item.icon" />
      <span>{{ item.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
.bottom {
  display: none;
}
@media (max-width: 991.98px) {
  .bottom {
    display: flex;
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 50;
    justify-content: space-around;
    align-items: flex-end;
    padding: 0.35rem 0.2rem calc(0.35rem + env(safe-area-inset-bottom, 0px));
    border-radius: 0;
    border-left: 0;
    border-right: 0;
    border-bottom: 0;
    background: color-mix(in srgb, var(--ci-bg-elevated) 88%, transparent);
    backdrop-filter: blur(18px) saturate(160%);
    -webkit-backdrop-filter: blur(18px) saturate(160%);
  }
  .item {
    flex: 1;
    border: 0;
    background: transparent;
    color: var(--ci-muted);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    gap: 0.12rem;
    font-size: 0.6rem;
    font-weight: 650;
    cursor: pointer;
    padding: 0.3rem 0.15rem;
    min-width: 0;
    -webkit-tap-highlight-color: transparent;
  }
  .item > span:last-child {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
  }
  .item i { font-size: 1.18rem; }
  .item.active { color: var(--ci-primary); }
  .item.fab { position: relative; top: -10px; }
  .fab-circle {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #3B82F6, #7C3AED);
    color: #fff;
    box-shadow: 0 10px 24px rgba(59, 130, 246, 0.45);
  }
  .fab-circle i { font-size: 1.2rem; }
}
@media (max-width: 360px) {
  .item { font-size: 0.55rem; }
  .fab-circle { width: 44px; height: 44px; }
}
</style>
