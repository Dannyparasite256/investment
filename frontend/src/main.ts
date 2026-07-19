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
