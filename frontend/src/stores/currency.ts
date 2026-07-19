import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '@/services/api'
import type { BalanceMoney, CurrencyOption, DisplayBalances } from '@/types/api'

const CODE_KEY = 'ci_display_currency'

export const useCurrencyStore = defineStore('currency', () => {
  const code = ref<string>(localStorage.getItem(CODE_KEY) || '')
  const options = ref<CurrencyOption[]>([])
  const balances = ref<DisplayBalances | null>(null)
  const loading = ref(false)
  const switching = ref(false)
  const error = ref('')

  const symbol = computed(() => balances.value?.available?.symbol || code.value || 'USD')
  const decimals = computed(() => {
    const s = symbol.value
    if (s === 'UGX') return 0
    if (['USD', 'EUR', 'GBP'].includes(s)) return 2
    return 4
  })

  function moneyLabel(m?: BalanceMoney | null) {
    if (!m) return '—'
    return m.label || `${m.formatted} ${m.symbol}`
  }

  async function loadOptions() {
    try {
      const { data } = await api.currencies()
      options.value = data.options || []
      if (!code.value && data.current) code.value = data.current
      else if (data.current) code.value = data.current
    } catch {
      /* ignore */
    }
  }

  async function refreshBalances(override?: string) {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.balances(override || code.value || undefined)
      if (data.ok === false) {
        error.value = data.error || 'Could not load balances'
        return null
      }
      balances.value = data as DisplayBalances
      if (data.currency) {
        code.value = data.currency
        localStorage.setItem(CODE_KEY, data.currency)
      }
      return data
    } catch (e: any) {
      error.value = e?.response?.data?.error || 'Balance load failed'
      return null
    } finally {
      loading.value = false
    }
  }

  async function setCurrency(next: string) {
    if (!next || next === code.value) {
      await refreshBalances(next)
      return
    }
    switching.value = true
    error.value = ''
    try {
      const { data } = await api.setDisplayCurrency(next)
      if (data.ok === false) {
        error.value = data.error || 'Invalid currency'
        return false
      }
      code.value = data.currency || next
      localStorage.setItem(CODE_KEY, code.value)
      document.cookie = `display_currency=${encodeURIComponent(code.value)};path=/;max-age=${60 * 60 * 24 * 400};samesite=lax`
      balances.value = data as DisplayBalances
      return true
    } catch (e: any) {
      error.value = e?.response?.data?.error || 'Could not change currency'
      return false
    } finally {
      switching.value = false
    }
  }

  async function init() {
    await loadOptions()
    await refreshBalances()
  }

  return {
    code,
    options,
    balances,
    loading,
    switching,
    error,
    symbol,
    decimals,
    moneyLabel,
    loadOptions,
    refreshBalances,
    setCurrency,
    init,
  }
})
