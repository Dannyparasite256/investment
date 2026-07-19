<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'

const route = useRoute()
const ui = useUiStore()
const transitionName = computed(() => (route.meta.public ? 'fade' : 'page'))
</script>

<template>
  <div class="app-root">
    <div v-if="ui.pageLoading" class="route-progress" aria-hidden="true">
      <div class="bar" />
    </div>
    <Toast position="top-right" />
    <ConfirmDialog />
    <router-view v-slot="{ Component }">
      <transition :name="transitionName" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100dvh;
}
.route-progress {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 9999;
  overflow: hidden;
}
.route-progress .bar {
  height: 100%;
  width: 35%;
  background: linear-gradient(90deg, #3B82F6, #7C3AED, #10B981);
  animation: slide 1s ease-in-out infinite;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.6);
}
@keyframes slide {
  0% { transform: translateX(-120%); }
  100% { transform: translateX(400%); }
}
</style>
