import { create } from 'zustand'
import { UserRole } from '@config'
import { jwtDecode } from 'jwt-decode'

type TokenPayload = { id: string; role: UserRole; tenant_id?: string }

type AuthState = {
  accessToken: string | null
  role: UserRole | null
  setAccessToken: (token: string) => void
  login: (args: { token: string }) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  role: null,
  setAccessToken: (token) => {
    let role: UserRole | null = null
    try {
      const decoded = jwtDecode<TokenPayload>(token)
      role = decoded.role
    } catch {}
    set({ accessToken: token, role })
  },
  login: ({ token }) => {
    let role: UserRole | null = null
    try {
      const decoded = jwtDecode<TokenPayload>(token)
      role = decoded.role
    } catch {}
    set({ accessToken: token, role })
  },
  logout: () => set({ accessToken: null, role: null }),
})) 