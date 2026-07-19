<script setup lang="ts">
import { onMounted } from 'vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppTopbar from '@/components/layout/AppTopbar.vue'
import AppBottomNav from '@/components/layout/AppBottomNav.vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const auth = useAuthStore()
const ui = useUiStore()

onMounted(() => {
  if (auth.token && !auth.user) auth.fetchMe()
})
</script>

<template>
  <div class="shell" :class="{ collapsed: ui.sidebarCollapsed }">
    <div
      class="overlay"
      :class="{ show: ui.sidebarOpen }"
      @click="ui.closeSidebar()"
    />
    <AppSidebar />
    <div class="main">
      <AppTopbar />
      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
    <AppBottomNav />
  </div>
</template>

<style scoped>
.shell {
  min-height: 100dvh;
  display: flex;
  padding: 12px;
  gap: 12px;
}
.overlay {
  display: none;
}
.main {
  flex: 1;
  min-width: 0;
  margin-left: var(--sidebar-w);
  display: flex;
  flex-direction: column;
  transition: margin-left 0.25s ease;
}
.shell.collapsed .main {
  margin-left: 88px;
}
.content {
  flex: 1;
  padding: 0.35rem 0.25rem 5.5rem;
  max-width: 1400px;
  width: 100%;
}
@media (min-width: 992px) {
  .content { padding-bottom: 2rem; }
}
@media (max-width: 991.98px) {
  .shell { padding: 0; gap: 0; }
  .main { margin-left: 0 !important; }
  .overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    z-index: 1030;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease;
  }
  .overlay.show {
    opacity: 1;
    pointer-events: auto;
  }
  .content {
    padding: 0.75rem 0.85rem 5.75rem;
  }
}
</style>
