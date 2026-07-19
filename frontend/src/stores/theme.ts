import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type ThemeMode = 'dark' | 'light' | 'glass' | 'classic'

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>((localStorage.getItem('ci_theme') as ThemeMode) || 'dark')

  function apply(m: ThemeMode) {
    mode.value = m
    const html = document.documentElement
    // Map glass/classic variants onto dark/light base + data-ui attribute
    if (m === 'light') {
      html.setAttribute('data-theme', 'light')
      html.setAttribute('data-ui', 'classic')
    } else if (m === 'glass') {
      html.setAttribute('data-theme', 'dark')
      html.setAttribute('data-ui', 'glass')
    } else if (m === 'classic') {
      html.setAttribute('data-theme', 'dark')
      html.setAttribute('data-ui', 'classic')
    } else {
      html.setAttribute('data-theme', 'dark')
      html.setAttribute('data-ui', 'premium')
    }
    localStorage.setItem('ci_theme', m)
  }

  function toggleDarkLight() {
    apply(mode.value === 'light' ? 'dark' : 'light')
  }

  // initial
  apply(mode.value)

  watch(mode, (m) => apply(m))

  return { mode, apply, toggleDarkLight }
})
