import { Routes, Route, Navigate } from 'react-router-dom'
import Landing from '@pages/Landing'
import Login from '@pages/Login'
import Signup from '@pages/Signup'
import TenantDashboard from '@pages/TenantDashboard'
import VehicleRates from '@pages/VehicleRates'
import TenantSettings from '@pages/TenantSettings'
import ProtectedRoute from '@components/ProtectedRoute'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route
        path="/tenant"
        element={
          <ProtectedRoute allowRoles={["tenant"]}>
            <TenantDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tenant/rates"
        element={
          <ProtectedRoute allowRoles={["tenant"]}>
            <VehicleRates />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tenant/settings"
        element={
          <ProtectedRoute allowRoles={["tenant"]}>
            <TenantSettings />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
} 