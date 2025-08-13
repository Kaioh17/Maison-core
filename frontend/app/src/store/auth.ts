import { create } from 'zustand'
import { UserRole } from '@config'
import { jwtDecode } from 'jwt-decode'

type TokenPayload = { id: string; role: UserRole; tenant_id?: string }

type AuthState = {
  accessToken: string | null
  role: UserRole | null
  userId: string | null
  setAccessToken: (token: string) => void
  login: (args: { token: string }) => void
  logout: () => void
  getUserId: () => string | null
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  role: null,
  userId: null,
  setAccessToken: (token) => {
    let role: UserRole | null = null
    let userId: string | null = null
    try {
      const decoded = jwtDecode<TokenPayload>(token)
      role = decoded.role
      userId = decoded.id
    } catch {}
    set({ accessToken: token, role, userId })
  },
  login: ({ token }) => {
    let role: UserRole | null = null
    let userId: string | null = null
    try {
      const decoded = jwtDecode<TokenPayload>(token)
      role = decoded.role
      userId = decoded.id
    } catch {}
    set({ accessToken: token, role, userId })
  },
  logout: () => set({ accessToken: null, role: null, userId: null }),
  getUserId: () => get().userId,
})) 