import { useEffect, useState } from 'react'
import { useAuthStore } from '@store/auth'

export default function AuthInitializer() {
  const [isInitialized, setIsInitialized] = useState(false)
  const { accessToken, role, checkAuthStatus, logout } = useAuthStore()

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // If we have a stored token, check if it's still valid
        if (accessToken && role) {
          const isValid = checkAuthStatus()
          
          if (!isValid) {
            // Token is invalid, clear it
            logout()
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
  }, [accessToken, role, checkAuthStatus, logout])

  // Show loading while initializing auth
  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return null
} 