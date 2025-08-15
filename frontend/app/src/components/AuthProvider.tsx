import { ReactNode, useEffect, useState } from 'react'
import { useAuthStore } from '@store/auth'
import { refreshTenantToken, refreshDriverToken, refreshRiderToken } from '@api/auth'
import { UserRole } from '@config'

interface AuthProviderProps {
  children: ReactNode
}

export default function AuthProvider({ children }: AuthProviderProps) {
  const { 
    accessToken, 
    role, 
    isAuthenticated, 
    setAccessToken, 
    logout, 
    checkAuthStatus 
  } = useAuthStore()
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if we have a stored token
        if (accessToken && role) {
          // Verify if the token is still valid
          const isValid = checkAuthStatus()
          
          if (!isValid) {
            // Token is invalid, try to refresh it
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
            } catch (refreshError) {
              // Refresh failed, logout user
              console.error('Token refresh failed:', refreshError)
              logout()
            }
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        logout()
      } finally {
        setIsInitialized(true)
      }
    }

    initializeAuth()
  }, [accessToken, role, setAccessToken, logout, checkAuthStatus])

  // Show loading while initializing auth
  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return <>{children}</>
} 