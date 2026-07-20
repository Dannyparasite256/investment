import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'
import type { User, Wallet } from '@/types/api'

const TOKEN_KEY = 'ci_token'

export type OtpChallenge = {
  method: 'email' | 'totp'
  detail: string
  emailFallback?: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<User | null>(null)
  const wallet = ref<Wallet | null>(null)
  const loading = ref(false)
  const error = ref('')
  const otpChallenge = ref<OtpChallenge | null>(null)
  const pendingEmail = ref('')
  const pendingPassword = ref('')

  const isAuthenticated = computed(() => !!token.value)
  const displayName = computed(() => {
    if (!user.value) return ''
    const n = `${user.value.first_name || ''} ${user.value.last_name || ''}`.trim()
    return n || user.value.email
  })

  function clearOtpState() {
    otpChallenge.value = null
    pendingEmail.value = ''
    pendingPassword.value = ''
  }

  async function login(
    email: string,
    password: string,
    opts?: { otp_code?: string; otp_method?: 'email' | 'totp'; resend_otp?: boolean },
  ) {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.login(email, password, opts)
      if (data.requires_otp && !data.token) {
        pendingEmail.value = email
        pendingPassword.value = password
        otpChallenge.value = {
          method: (data.method as 'email' | 'totp') || 'email',
          detail: data.detail || 'Enter the verification code.',
          emailFallback: !!data.email_fallback,
        }
        if (data.detail) {
          // informational, not always an error
        }
        return { ok: false, needsOtp: true as const }
      }
      if (!data.token) {
        error.value = data.detail || 'Login failed'
        return { ok: false, needsOtp: false as const }
      }
      token.value = data.token
      localStorage.setItem(TOKEN_KEY, data.token)
      user.value = data.user
      clearOtpState()
      await fetchMe()
      return { ok: true, needsOtp: false as const }
    } catch (e: any) {
      const d = e?.response?.data
      if (d?.requires_otp) {
        pendingEmail.value = email
        pendingPassword.value = password
        otpChallenge.value = {
          method: (d.method as 'email' | 'totp') || 'email',
          detail: d.detail || 'Enter the verification code.',
          emailFallback: !!d.email_fallback,
        }
        error.value = d.detail || 'Invalid code'
        return { ok: false, needsOtp: true as const }
      }
      error.value = d?.non_field_errors?.[0]
        || d?.detail
        || 'Invalid email or password'
      return { ok: false, needsOtp: false as const }
    } finally {
      loading.value = false
    }
  }

  async function verifyOtp(code: string, method?: 'email' | 'totp') {
    if (!pendingEmail.value || !pendingPassword.value) {
      error.value = 'Session expired. Enter your password again.'
      clearOtpState()
      return false
    }
    const m = method || otpChallenge.value?.method || 'email'
    const result = await login(pendingEmail.value, pendingPassword.value, {
      otp_code: code,
      otp_method: m,
    })
    return result.ok
  }

  async function resendEmailOtp() {
    if (!pendingEmail.value || !pendingPassword.value) {
      error.value = 'Session expired. Enter your password again.'
      return false
    }
    error.value = ''
    const result = await login(pendingEmail.value, pendingPassword.value, {
      otp_method: 'email',
      resend_otp: true,
    })
    return result.needsOtp
  }

  async function requestEmailOtpFallback() {
    if (!pendingEmail.value || !pendingPassword.value) {
      error.value = 'Session expired. Enter your password again.'
      return false
    }
    const result = await login(pendingEmail.value, pendingPassword.value, {
      otp_method: 'email',
    })
    return result.needsOtp
  }

  async function register(payload: {
    email: string
    password: string
    first_name?: string
    last_name?: string
    referral_code?: string
  }) {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.register(payload)
      token.value = data.token
      localStorage.setItem(TOKEN_KEY, data.token)
      user.value = data.user
      await fetchMe()
      return true
    } catch (e: any) {
      error.value = e?.response?.data?.email?.[0]
        || e?.response?.data?.detail
        || 'Registration failed'
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
    clearOtpState()
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
    otpChallenge,
    isAuthenticated,
    displayName,
    login,
    verifyOtp,
    resendEmailOtp,
    requestEmailOtpFallback,
    clearOtpState,
    register,
    fetchMe,
    refreshWallet,
    logout,
  }
})
