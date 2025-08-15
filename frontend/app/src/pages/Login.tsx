import React, { useState, useEffect } from 'react'
import { Eye, EyeOff, Mail, Lock, Car, ArrowRight } from 'lucide-react'
import { loginTenant } from '@api/auth'
import { useAuthStore } from '@store/auth'
import { useNavigate, useLocation } from 'react-router-dom'

export default function AuthPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({ email: '', password: '' })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated, role } = useAuthStore()

  // Redirect authenticated users
  useEffect(() => {
    if (isAuthenticated && role) {
      const from = location.state?.from?.pathname || getDefaultRoute(role)
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, role, navigate, location])

  const getDefaultRoute = (userRole: string) => {
    switch (userRole) {
      case 'tenant':
        return '/tenant'
      case 'driver':
        return '/driver'
      case 'rider':
        return '/rider'
      case 'admin':
        return '/admin'
      default:
        return '/'
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, [e.target.name]: e.target.value })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setIsLoading(true)
      setError('')
      const data = await loginTenant(formData.email, formData.password)
      useAuthStore.getState().login({ token: data.access_token })
      // Navigation will be handled by the useEffect above
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateAccount = () => {
    navigate('/signup')
  }

  // Don't render if already authenticated
  if (isAuthenticated) {
    return null
  }

  return (
    <main className="bw" aria-label="Auth">
      <div className="bw-container bw-auth">
        <div className="bw-auth-card bw-card" role="form" aria-labelledby="auth-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <div style={{ width: 40, height: 40, border: '1px solid var(--bw-border-strong)', display: 'grid', placeItems: 'center', borderRadius: 2 }}>
              <Car size={18} aria-hidden />
            </div>
            <h1 id="auth-title" style={{ margin: 0, fontSize: 22 }}>Maison</h1>
          </div>

          <h2 style={{ margin: 0, fontSize: 28 }}>Welcome back</h2>
          <p className="small-muted" style={{ marginTop: 6 }}>Sign in to continue</p>

          {error && (
            <div style={{ 
              marginTop: 16, 
              padding: '12px', 
              backgroundColor: '#fee2e2', 
              border: '1px solid #fecaca', 
              borderRadius: '4px',
              color: '#dc2626',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ marginTop: 16 }}>
            <label className="small-muted" htmlFor="email">Email</label>
            <div style={{ position: 'relative', marginTop: 6, marginBottom: 12 }}>
              <Mail size={16} aria-hidden style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', opacity: .7 }} />
              <input id="email" name="email" type="email" required className="bw-input" style={{ paddingLeft: 36 }} placeholder="you@email" onChange={handleInputChange} />
            </div>

            <label className="small-muted" htmlFor="password">Password</label>
            <div style={{ position: 'relative', marginTop: 6 }}>
              <Lock size={16} aria-hidden style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', opacity: .7 }} />
              <input id="password" name="password" type={showPassword ? 'text' : 'password'} required className="bw-input" style={{ paddingLeft: 36, paddingRight: 36 }} placeholder="••••••••" onChange={handleInputChange} />
              <button type="button" aria-label="Toggle password" onClick={() => setShowPassword(!showPassword)} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 0, color: '#fff' }}>
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            <button 
              className="bw-btn" 
              style={{ width: '100%', marginTop: 16 }} 
              disabled={isLoading}
            >
              <span>{isLoading ? 'Signing in...' : 'Sign in'}</span>
              {!isLoading && <ArrowRight size={16} aria-hidden />}
            </button>

            <div style={{ marginTop: 12, textAlign: 'center' }}>
              <span className="small-muted">Don't have an account? </span>
              <button 
                type="button" 
                className="bw-btn-outline" 
                style={{ padding: '4px 8px', marginLeft: 6 }} 
                onClick={handleCreateAccount}
              >
                Create one
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
} 