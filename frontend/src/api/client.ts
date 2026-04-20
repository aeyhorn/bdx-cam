import axios from 'axios'

/**
 * API base URL from Vite env. If unset, axios uses relative `/api/v1/...` URLs against the
 * current page origin (correct for Docker: UI on :8080 proxies `/api` to the backend).
 *
 * If the bundle was built with `VITE_API_URL=http://localhost:8000` but the app is opened
 * via another host (e.g. http://192.168.x.x:8080), requests would wrongly hit the client
 * machine's localhost and often return 404 "Not Found". In that case we fall back to
 * same-origin (empty base URL).
 */
function resolveApiBaseURL(): string {
  const raw = import.meta.env.VITE_API_URL?.trim() || ''
  if (typeof window === 'undefined') return raw
  const pageHost = window.location.hostname
  const pageIsLocal = pageHost === 'localhost' || pageHost === '127.0.0.1'
  const targetsLocalApi =
    raw === 'http://localhost:8000' ||
    raw === 'http://127.0.0.1:8000' ||
    raw.startsWith('http://localhost:8000/') ||
    raw.startsWith('http://127.0.0.1:8000/')
  if (!pageIsLocal && targetsLocalApi) return ''
  return raw
}

const baseURL = resolveApiBaseURL()

export const api = axios.create({
  baseURL: baseURL || undefined,
  headers: { 'Content-Type': 'application/json' },
})

export function getStoredTokens(): { access: string | null; refresh: string | null } {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  }
}

export function setStoredTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

export function clearStoredTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

api.interceptors.request.use((config) => {
  const { access } = getStoredTokens()
  if (access) {
    config.headers.Authorization = `Bearer ${access}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const { refresh } = getStoredTokens()
      if (refresh) {
        try {
          const { data } = await axios.post(`${baseURL || ''}/api/v1/auth/refresh`, { refresh_token: refresh })
          setStoredTokens(data.access_token, data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          clearStoredTokens()
        }
      }
    }
    return Promise.reject(error)
  }
)
