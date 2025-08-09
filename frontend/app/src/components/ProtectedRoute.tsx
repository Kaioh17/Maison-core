import { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@store/auth'
import { UserRole } from '@config'

export default function ProtectedRoute({ allowRoles, children }: { allowRoles: UserRole[]; children: ReactNode }) {
  const { accessToken, role } = useAuthStore()
  const location = useLocation()

  if (!accessToken) return <Navigate to="/login" state={{ from: location }} replace />
  if (role && !allowRoles.includes(role)) return <Navigate to="/login" replace />
  return <>{children}</>
} 