import React, { useState } from 'react'
import { Eye, EyeOff, Mail, Lock, Car, ArrowRight } from 'lucide-react'
import { loginTenant } from '@api/auth'
import { useAuthStore } from '@store/auth'
import { useNavigate } from 'react-router-dom'

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [formData, setFormData] = useState({ email: '', password: '', confirmPassword: '' })
  const navigate = useNavigate()

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, [e.target.name]: e.target.value })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isLogin) {
      const data = await loginTenant(formData.email, formData.password)
      useAuthStore.getState().login({ token: data.access_token })
      navigate('/tenant')
    } else {
      navigate('/signup')
    }
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

          <h2 style={{ margin: 0, fontSize: 28 }}>{isLogin ? 'Welcome back' : 'Create your account'}</h2>
          <p className="small-muted" style={{ marginTop: 6 }}>{isLogin ? 'Sign in to continue' : 'Set up your company profile'}</p>

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

            {!isLogin && (
              <div style={{ marginTop: 12 }}>
                <label className="small-muted" htmlFor="confirmPassword">Confirm password</label>
                <div style={{ position: 'relative', marginTop: 6 }}>
                  <Lock size={16} aria-hidden style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', opacity: .7 }} />
                  <input id="confirmPassword" name="confirmPassword" type={showConfirmPassword ? 'text' : 'password'} className="bw-input" style={{ paddingLeft: 36, paddingRight: 36 }} placeholder="••••••••" onChange={handleInputChange} />
                  <button type="button" aria-label="Toggle confirm password" onClick={() => setShowConfirmPassword(!showConfirmPassword)} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 0, color: '#fff' }}>
                    {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
            )}

            <button className="bw-btn" style={{ width: '100%', marginTop: 16 }}>
              <span>{isLogin ? 'Sign in' : 'Create account'}</span>
              <ArrowRight size={16} aria-hidden />
            </button>

            <div style={{ marginTop: 12, textAlign: 'center' }}>
              <span className="small-muted">{isLogin ? "Don't have an account? " : 'Already registered? '}</span>
              <button type="button" className="bw-btn-outline" style={{ padding: '4px 8px', marginLeft: 6 }} onClick={() => setIsLogin(!isLogin)}>
                {isLogin ? 'Create one' : 'Sign in'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
} 