import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL?.trim() || ''

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
