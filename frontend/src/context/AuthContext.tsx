import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

export interface User {
  id: string
  email: string
  prenom: string | null
  email_verified: boolean
}

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, prenom: string, consentCgu: boolean) => Promise<void>
  logout: () => Promise<void>
  authFetch: (input: string, init?: RequestInit) => Promise<Response>
}

const AuthContext = createContext<AuthContextValue | null>(null)

async function readError(res: Response): Promise<string> {
  const body = await res.json().catch(() => null)
  return body?.detail || "Une erreur est survenue, réessayez."
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function tryRefresh(): Promise<string | null> {
    const res = await fetch('/api/auth/refresh', { method: 'POST', credentials: 'include' })
    if (!res.ok) {
      setUser(null)
      setAccessToken(null)
      return null
    }
    const data = await res.json()
    setAccessToken(data.access_token)
    setUser(data.user)
    return data.access_token as string
  }

  useEffect(() => {
    tryRefresh().finally(() => setLoading(false))
  }, [])

  async function login(email: string, password: string) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) throw new Error(await readError(res))
    const data = await res.json()
    setAccessToken(data.access_token)
    setUser(data.user)
  }

  async function register(email: string, password: string, prenom: string, consentCgu: boolean) {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, prenom: prenom || undefined, consent_cgu: consentCgu }),
    })
    if (!res.ok) throw new Error(await readError(res))
    const data = await res.json()
    setAccessToken(data.access_token)
    setUser(data.user)
  }

  async function logout() {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
    setUser(null)
    setAccessToken(null)
  }

  async function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
    const doFetch = (token: string | null) =>
      fetch(input, {
        ...init,
        credentials: 'include',
        headers: {
          ...(init.headers || {}),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      })

    let res = await doFetch(accessToken)
    if (res.status === 401) {
      const newToken = await tryRefresh()
      if (newToken) res = await doFetch(newToken)
    }
    return res
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, authFetch }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth doit être utilisé dans un AuthProvider')
  return ctx
}
