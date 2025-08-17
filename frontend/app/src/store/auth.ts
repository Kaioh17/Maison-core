import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { UserRole } from '@config'
import { jwtDecode } from 'jwt-decode'

type TokenPayload = { id: string; role: UserRole; tenant_id?: string }

type AuthState = {
  accessToken: string | null
  role: UserRole | null
  userId: string | null
  tenantId: string | null
  isAuthenticated: boolean
  setAccessToken: (token: string) => void
  login: (args: { token: string }) => void
  logout: () => void
  getUserId: () => string | null
  getTenantId: () => string | null
  checkAuthStatus: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      role: null,
      userId: null,
      tenantId: null,
      isAuthenticated: false,
      setAccessToken: (token) => {
        let role: UserRole | null = null
        let userId: string | null = null
        let tenantId: string | null = null
        try {
          const decoded = jwtDecode<TokenPayload>(token)
          role = decoded.role
          userId = decoded.id
          tenantId = decoded.tenant_id || null
        } catch {}
        set({ 
          accessToken: token, 
          role, 
          userId, 
          tenantId,
          isAuthenticated: !!token 
        })
      },
      login: ({ token }) => {
        let role: UserRole | null = null
        let userId: string | null = null
        let tenantId: string | null = null
        try {
          const decoded = jwtDecode<TokenPayload>(token)
          role = decoded.role
          userId = decoded.id
          tenantId = decoded.tenant_id || null
        } catch {}
        set({ 
          accessToken: token, 
          role, 
          userId, 
          tenantId,
          isAuthenticated: true 
        })
      },
      logout: () => set({ 
        accessToken: null, 
        role: null, 
        userId: null, 
        tenantId: null,
        isAuthenticated: false 
      }),
      getUserId: () => get().userId,
      getTenantId: () => get().tenantId,
      checkAuthStatus: () => {
        const state = get()
        if (!state.accessToken) return false
        
        try {
          const decoded = jwtDecode<TokenPayload>(state.accessToken)
          const currentTime = Date.now() / 1000
          
          if (decoded.exp && decoded.exp < currentTime) {
            get().logout()
            return false
          }
          
          return true
        } catch {
          get().logout()
          return false
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        role: state.role,
        userId: state.userId,
        tenantId: state.tenantId,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
) 