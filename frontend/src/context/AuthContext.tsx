import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react'

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

  // UN SEUL RAFRAICHISSEMENT A LA FOIS. Le jeton de rafraichissement est a USAGE UNIQUE
  // (`routers/auth.py` : « un refresh token ne sert qu'une fois ») : deux appels concurrents
  // se detruisent l'un l'autre — le premier consomme le jeton, le second presente un jeton
  // deja revoque, recoit 401, et son `setUser(null)` efface la session que le premier venait
  // de retablir. Celui qui repond en dernier gagne, donc l'utilisateur est deconnecte au
  // hasard. C'etait tres visible sur /admin, dont le tableau de bord interroge plusieurs
  // endpoints en parallele, et double en developpement par le `StrictMode` de `main.tsx`
  // qui execute les effets deux fois : 11 appels pour UN chargement de page, mesures.
  //
  // On garde donc la promesse en cours et tout le monde attend la meme. Ne pas remplacer
  // par un simple drapeau booleen : les appelants ont besoin du jeton, pas seulement de
  // savoir qu'un appel est parti.
  const refreshEnCours = useRef<Promise<string | null> | null>(null)

  function tryRefresh(): Promise<string | null> {
    if (refreshEnCours.current) return refreshEnCours.current

    const promesse = (async () => {
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
    })()

    refreshEnCours.current = promesse
    // Libere des que c'est fini : un 401 PLUS TARD doit pouvoir relancer un vrai
    // rafraichissement, on ne met pas le mecanisme en cache pour la session.
    promesse.finally(() => {
      if (refreshEnCours.current === promesse) refreshEnCours.current = null
    })
    return promesse
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
