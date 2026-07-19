import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ToastItem {
  id: number
  title: string
  message?: string
  severity: 'success' | 'info' | 'warn' | 'error'
  life?: number
}

export const useUiStore = defineStore('ui', () => {
  const sidebarOpen = ref(false)
  const sidebarCollapsed = ref(false)
  const pageLoading = ref(false)
  const toasts = ref<ToastItem[]>([])
  let seq = 1

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }
  function closeSidebar() {
    sidebarOpen.value = false
  }
  function toggleCollapse() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function toast(title: string, message = '', severity: ToastItem['severity'] = 'info', life = 4200) {
    const id = seq++
    toasts.value.push({ id, title, message, severity, life })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, life)
  }

  function setLoading(v: boolean) {
    pageLoading.value = v
  }

  return {
    sidebarOpen,
    sidebarCollapsed,
    pageLoading,
    toasts,
    toggleSidebar,
    closeSidebar,
    toggleCollapse,
    toast,
    setLoading,
  }
})
