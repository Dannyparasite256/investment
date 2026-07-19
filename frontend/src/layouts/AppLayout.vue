<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppTopbar from '@/components/layout/AppTopbar.vue'
import AppBottomNav from '@/components/layout/AppBottomNav.vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { api } from '@/services/api'

const auth = useAuthStore()
const ui = useUiStore()
const router = useRouter()
const banner = ref('')
const showOnboarding = ref(false)

onMounted(async () => {
  if (auth.token && !auth.user) await auth.fetchMe()
  try {
    const { data } = await api.bootstrap()
    banner.value = data.announcement || ''
    const o = data.onboarding
    if (o && !o.tour_completed && !(o.has_deposit && o.has_investment && o.kyc_done && o.two_fa_done)) {
      showOnboarding.value = true
    }
    try {
      localStorage.setItem('ci_bootstrap', JSON.stringify(data))
    } catch { /* */ }
  } catch { /* */ }
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
      <div v-if="banner" class="site-banner" @click="router.push('/announcements')">
        <i class="pi pi-megaphone" />
        <span>{{ banner }}</span>
      </div>
      <div v-if="showOnboarding" class="onboard-hint" @click="router.push('/onboarding')">
        Finish setup checklist →
      </div>
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
.site-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  padding: 0.55rem 0.85rem;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  font-size: 0.88rem;
  cursor: pointer;
}
.onboard-hint {
  margin-bottom: 0.5rem;
  padding: 0.45rem 0.85rem;
  border-radius: 999px;
  background: rgba(37, 211, 102, 0.12);
  color: #25D366;
  font-size: 0.82rem;
  font-weight: 650;
  cursor: pointer;
  width: fit-content;
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
