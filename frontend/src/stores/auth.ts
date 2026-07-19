import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'
import type { User, Wallet } from '@/types/api'

const TOKEN_KEY = 'ci_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<User | null>(null)
  const wallet = ref<Wallet | null>(null)
  const loading = ref(false)
  const error = ref('')

  const isAuthenticated = computed(() => !!token.value)
  const displayName = computed(() => {
    if (!user.value) return ''
    const n = `${user.value.first_name || ''} ${user.value.last_name || ''}`.trim()
    return n || user.value.email
  })

  async function login(email: string, password: string) {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.login(email, password)
      token.value = data.token
      localStorage.setItem(TOKEN_KEY, data.token)
      user.value = data.user
      await fetchMe()
      return true
    } catch (e: any) {
      error.value = e?.response?.data?.non_field_errors?.[0]
        || e?.response?.data?.detail
        || 'Invalid email or password'
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const { data } = await api.me()
      user.value = data.user
      wallet.value = data.wallet
    } catch {
      logout(false)
    }
  }

  async function refreshWallet() {
    if (!token.value) return
    try {
      const { data } = await api.wallet()
      wallet.value = data
    } catch {
      /* ignore */
    }
  }

  function logout(redirect = true) {
    token.value = null
    user.value = null
    wallet.value = null
    localStorage.removeItem(TOKEN_KEY)
    const base = import.meta.env.BASE_URL || '/'
    const loginPath = `${base}login`.replace(/\/{2,}/g, '/').replace(':/', '://')
    if (redirect && !window.location.pathname.includes('/login')) {
      window.location.href = loginPath
    }
  }

  return {
    token,
    user,
    wallet,
    loading,
    error,
    isAuthenticated,
    displayName,
    login,
    fetchMe,
    refreshWallet,
    logout,
  }
})
