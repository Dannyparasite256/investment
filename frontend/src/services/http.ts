import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 30000,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Token ${auth.token}`
  }
  // CSRF for session-auth endpoints
  const csrf = document.cookie
    .split(';')
    .map((c) => c.trim())
    .find((c) => c.startsWith('csrftoken='))
  if (csrf) {
    config.headers['X-CSRFToken'] = decodeURIComponent(csrf.split('=').slice(1).join('='))
  }
  return config
})

http.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401) {
      const auth = useAuthStore()
      auth.logout(false)
      if (!window.location.pathname.includes('/login')) {
        const base = import.meta.env.BASE_URL || '/'
        const login = `${base}login`.replace(/\/{2,}/g, '/').replace(':/', '://')
        window.location.href = `${login}?next=${encodeURIComponent(window.location.pathname)}`
      }
    }
    return Promise.reject(error)
  },
)

export default http
