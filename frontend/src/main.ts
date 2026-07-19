import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'
import VueApexCharts from 'vue3-apexcharts'

import 'primeicons/primeicons.css'
import '@/assets/main.css'

import App from './App.vue'
import router from './router'
import { useThemeStore } from './stores/theme'

/**
 * One-time hard refresh after deploys that change SPA assets.
 * PythonAnywhere clients often keep an old service-worker cache of /app/.
 */
const CACHE_BUST = 'crypto-icons-v4'
async function bustStaleAppCache() {
  try {
    if (localStorage.getItem('ci_cache_bust') === CACHE_BUST) return
    localStorage.setItem('ci_cache_bust', CACHE_BUST)
    if ('serviceWorker' in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations()
      await Promise.all(regs.map((r) => r.unregister()))
    }
    if (typeof caches !== 'undefined') {
      const keys = await caches.keys()
      await Promise.all(keys.map((k) => caches.delete(k)))
    }
    // Reload once so the next load uses fresh /app/assets/*
    window.location.reload()
  } catch {
    /* ignore */
  }
}
void bustStaleAppCache()

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      darkModeSelector: 'html[data-theme="dark"], html[data-ui="premium"], html[data-ui="glass"]',
      cssLayer: false,
    },
  },
  ripple: true,
})
app.use(ToastService)
app.use(ConfirmationService)
app.use(VueApexCharts)
app.directive('tooltip', Tooltip)

useThemeStore()

app.mount('#app')
