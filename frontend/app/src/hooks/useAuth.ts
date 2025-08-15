import { useCallback, useEffect } from 'react'
import { jwtDecode } from 'jwt-decode'
import { useAuthStore } from '@store/auth'
import { refreshTenantToken, refreshDriverToken, refreshRiderToken } from '@api/auth'
import { UserRole } from '@config'

export const useAuth = () => {
  const {
    accessToken,
    role,
    userId,
    tenantId,
    isAuthenticated,
    setAccessToken,
    login,
    logout,
    checkAuthStatus
  } = useAuthStore()

  const refreshToken = useCallback(async () => {
    if (!role) return null

    try {
      let newToken: string
      
      switch (role) {
        case 'tenant':
          const tenantResponse = await refreshTenantToken()
          newToken = tenantResponse.new_access_token
          break
        case 'driver':
          const driverResponse = await refreshDriverToken()
          newToken = driverResponse.new_access_token
          break
        case 'rider':
          const riderResponse = await refreshRiderToken()
          newToken = riderResponse.new_access_token
          break
        default:
          throw new Error('Unknown role')
      }
      
      setAccessToken(newToken)
      return newToken
    } catch (error) {
      console.error('Token refresh failed:', error)
      logout()
      return null
    }
  }, [role, setAccessToken, logout])

  const isTokenExpired = useCallback(() => {
    if (!accessToken) return true
    
    try {
      const decoded = jwtDecode(accessToken) as any
      const currentTime = Date.now() / 1000
      return decoded.exp && decoded.exp < currentTime
    } catch {
      return true
    }
  }, [accessToken])

  useEffect(() => {
    // Check token validity on mount and when token changes
    if (accessToken && isTokenExpired()) {
      logout()
    }
  }, [accessToken, isTokenExpired, logout])

  return {
    accessToken,
    role,
    userId,
    tenantId,
    isAuthenticated,
    login,
    logout,
    refreshToken,
    checkAuthStatus,
    isTokenExpired
  }
} 