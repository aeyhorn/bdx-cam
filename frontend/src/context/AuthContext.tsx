import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, clearStoredTokens, getStoredTokens, setStoredTokens } from '../api/client'

export type RoleKey = 'ADMIN' | 'FEEDBACK_PRODUCTION' | 'ENGINEERING'

export type UserMe = {
  id: number
  first_name: string
  last_name: string
  email: string
  role_id: number
  is_active: boolean
  role: { id: number; key: RoleKey; name: string }
}

type AuthState = {
  user: UserMe | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshMe: () => Promise<void>
}

const AuthContext = createContext<AuthState | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserMe | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshMe = useCallback(async () => {
    const { access } = getStoredTokens()
    if (!access) {
      setUser(null)
      return
    }
    const { data } = await api.get<UserMe>('/api/v1/auth/me')
    setUser(data)
  }, [])

  useEffect(() => {
    refreshMe()
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [refreshMe])

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await api.post<{ access_token: string; refresh_token: string }>('/api/v1/auth/login', {
      email,
      password,
    })
    setStoredTokens(data.access_token, data.refresh_token)
    await refreshMe()
  }, [refreshMe])

  const logout = useCallback(async () => {
    try {
      await api.post('/api/v1/auth/logout')
    } catch {
      /* ignore */
    }
    clearStoredTokens()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, logout, refreshMe }),
    [user, loading, login, logout, refreshMe]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth outside AuthProvider')
  return ctx
}
