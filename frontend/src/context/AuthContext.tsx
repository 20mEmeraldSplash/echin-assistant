import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import * as api from '../api'

type User = { id: number; email: string } | null

type AuthContextValue = {
  user: User
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User>(null)
  const [loading, setLoading] = useState(true)

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const u = await api.me()
      setUser(u)
    } catch {
      localStorage.removeItem('token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.login(email, password)
    localStorage.setItem('token', access_token)
    await loadUser()
  }, [loadUser])

  const signup = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.signup(email, password)
    localStorage.setItem('token', access_token)
    await loadUser()
  }, [loadUser])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
