# Authentication Implementation Guide

This document explains how the authentication system works in the Maison frontend application, specifically focusing on persistent sessions and refresh token functionality for tenants.

## Overview

The authentication system provides:
- Persistent login sessions using localStorage
- Automatic token refresh when access tokens expire
- Secure token storage with automatic cleanup
- Role-based access control
- Automatic redirects for authenticated/unauthenticated users

## Key Components

### 1. Auth Store (`src/store/auth.ts`)

The central authentication state management using Zustand with persistence:

```typescript
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
```

**Features:**
- Automatic token validation on app startup
- Persistent storage across browser sessions
- Automatic token expiration checking
- Role-based user identification

### 2. HTTP Interceptor (`src/api/http.ts`)

Handles automatic token refresh and request authentication:

```typescript
// Automatically adds Authorization header to requests
http.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Automatically refreshes expired tokens
http.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Attempt token refresh
      const newToken = await refreshToken()
      if (newToken) {
        // Retry original request with new token
        return http(originalRequest)
      }
    }
    return Promise.reject(error)
  }
)
```

### 3. Auth Initializer (`src/components/AuthInitializer.tsx`)

Handles authentication state restoration on app startup:

```typescript
export default function AuthInitializer() {
  useEffect(() => {
    const initializeAuth = async () => {
      if (accessToken && role) {
        const isValid = checkAuthStatus()
        if (!isValid) {
          logout()
        }
      }
    }
    initializeAuth()
  }, [])
  
  // Shows loading spinner while checking auth
  return isInitialized ? null : <LoadingSpinner />
}
```

### 4. Protected Route (`src/components/ProtectedRoute.tsx`)

Route protection with automatic redirects:

```typescript
export default function ProtectedRoute({ allowRoles, children }) {
  const { accessToken, role, isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated || !accessToken) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  
  if (role && !allowRoles.includes(role)) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}
```

## Authentication Flow

### 1. Login Process

```typescript
const handleLogin = async (email: string, password: string) => {
  try {
    const response = await loginTenant(email, password)
    const { access_token } = response.data
    
    // Store token and user info
    useAuthStore.getState().login({ token: access_token })
    
    // User is automatically redirected to dashboard
  } catch (error) {
    // Handle login errors
  }
}
```

### 2. Token Refresh Process

When an API request returns 401 (Unauthorized):

1. HTTP interceptor catches the error
2. Automatically calls the appropriate refresh endpoint based on user role
3. Updates the stored access token
4. Retries the original request with the new token
5. If refresh fails, user is logged out

### 3. Session Persistence

- Tokens are stored in localStorage using Zustand's persist middleware
- On app startup, `AuthInitializer` checks stored tokens
- Valid tokens restore the user session automatically
- Expired tokens are automatically cleared

## Backend Integration

### Required Endpoints

The frontend expects these backend endpoints:

```typescript
// Login endpoints
POST /api/v1/login/tenants
POST /api/v1/login/driver  
POST /api/v1/login/user

// Refresh endpoints
POST /api/v1/login/refresh_tenants
POST /api/v1/login/refresh

// Response format for refresh
{
  "new_access_token": "string"
}
```

### Cookie Configuration

Refresh tokens are sent via HTTP-only cookies:

```typescript
// Backend should set refresh token cookie
response.set_cookie(
  key="refresh_token",
  value=refresh_token,
  httponly=True,
  secure=False, // Set to true in production
  samesite="lax",
  max_age=60 * 60 * 24 * 30, // 30 days
  path="/api/v1/login/refresh_tenants"
)
```

## Usage Examples

### Checking Authentication Status

```typescript
import { useAuthStore } from '@store/auth'

function MyComponent() {
  const { isAuthenticated, role, userId } = useAuthStore()
  
  if (!isAuthenticated) {
    return <div>Please log in</div>
  }
  
  return <div>Welcome, {role} {userId}!</div>
}
```

### Using the Auth Hook

```typescript
import { useAuth } from '@hooks/useAuth'

function MyComponent() {
  const { 
    isAuthenticated, 
    role, 
    logout, 
    refreshToken 
  } = useAuth()
  
  const handleLogout = () => {
    logout()
    // User is automatically redirected to login
  }
  
  const handleRefresh = async () => {
    await refreshToken()
  }
  
  return (
    <div>
      <button onClick={handleLogout}>Logout</button>
      <button onClick={handleRefresh}>Refresh Token</button>
    </div>
  )
}
```

### Protecting Routes

```typescript
import ProtectedRoute from '@components/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/tenant" element={
        <ProtectedRoute allowRoles={["tenant"]}>
          <TenantDashboard />
        </ProtectedRoute>
      } />
    </Routes>
  )
}
```

## Security Features

1. **HTTP-Only Cookies**: Refresh tokens are stored in HTTP-only cookies, preventing XSS attacks
2. **Automatic Cleanup**: Expired tokens are automatically removed
3. **Secure Storage**: Access tokens are stored in memory and localStorage with automatic validation
4. **Role-Based Access**: Routes are protected based on user roles
5. **Automatic Logout**: Users are automatically logged out when refresh tokens fail

## Troubleshooting

### Common Issues

1. **Tokens not persisting**: Check if localStorage is enabled and not blocked
2. **Refresh not working**: Verify backend refresh endpoints are working and cookies are set correctly
3. **Infinite redirects**: Ensure login page doesn't redirect authenticated users
4. **Type errors**: Make sure all dependencies are installed and TypeScript is configured correctly

### Debug Mode

Enable debug logging in the HTTP interceptor:

```typescript
console.log('🚀 HTTP Request:', { method, url, hasToken })
console.log('✅ HTTP Response:', { status, url, data })
console.log('❌ HTTP Error:', { status, message, response })
```

## Testing

To test the authentication flow:

1. Login with valid credentials
2. Check that tokens are stored in localStorage
3. Refresh the page - user should remain logged in
4. Wait for token expiration or manually expire token
5. Verify automatic refresh works
6. Test logout functionality

## Production Considerations

1. **HTTPS**: Set `secure: true` for cookies in production
2. **Token Expiration**: Configure appropriate token lifetimes
3. **Rate Limiting**: Implement rate limiting on refresh endpoints
4. **Monitoring**: Add logging for authentication failures
5. **Error Handling**: Implement proper error boundaries for auth failures 