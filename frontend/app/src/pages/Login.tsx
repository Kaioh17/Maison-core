import React, { useState } from 'react'
import { Eye, EyeOff, Mail, Lock, Car, ArrowRight } from 'lucide-react'
import { loginTenant } from '@api/auth'
import { useAuthStore } from '@store/auth'
import { useNavigate } from 'react-router-dom'

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
  })

  const navigate = useNavigate()

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

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
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg,#ffffff,#f6f6f9)' }}>
      <div className="container" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32 }}>
        {/* Left Branding */}
        <div className="vstack" style={{ justifyContent: 'center' }}>
          <div className="hstack" style={{ gap: 12, alignItems: 'center' }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: 'linear-gradient(135deg,#c7a024,#f3df87)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Car color="#111" size={22} />
            </div>
            <h1 style={{ fontSize: 36, margin: 0, background: 'linear-gradient(90deg,#111,#555)', WebkitBackgroundClip: 'text', color: 'transparent' }}>Maison</h1>
          </div>
          <h2 style={{ fontSize: 48, margin: '12px 0 0 0', lineHeight: 1.1 }}>Luxury Transportation <span style={{ background: 'linear-gradient(90deg,#c7a024,#f3df87)', WebkitBackgroundClip: 'text', color: 'transparent' }}>Redefined</span></h2>
          <p style={{ color: '#4b5563', fontSize: 18, maxWidth: 560 }}>
            Experience premium car services with enterprise‑grade technology. Built for luxury, designed for scale.
          </p>
          <div className="small">Multi‑brand operations • Real‑time fleet • Premium CX</div>
        </div>

        {/* Right Auth */}
        <div style={{ maxWidth: 460, marginLeft: 'auto' }}>
          <div style={{ background: 'rgba(255,255,255,0.8)', backdropFilter: 'blur(10px)', border: '1px solid #e5e7eb', borderRadius: 20, padding: 24, boxShadow: '0 10px 30px rgba(17,24,39,0.08)' }}>
            <div style={{ textAlign: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: 28, color: '#111827' }}>{isLogin ? 'Welcome Back' : 'Create Your Account'}</h3>
              <div className="small" style={{ color: '#6b7280' }}>{isLogin ? 'Sign in to your account' : 'Create your premium account'}</div>
            </div>

            <form className="vstack" onSubmit={handleSubmit}>
              <div>
                <label className="small" style={{ color: '#374151' }}>Email Address</label>
                <div style={{ position: 'relative' }}>
                  <Mail style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#6b7280' }} size={18} />
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="input"
                    style={{ paddingLeft: 36, background: '#fff', borderColor: '#e5e7eb', color: '#111' }}
                    placeholder="you@email.com"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="small" style={{ color: '#374151' }}>Password</label>
                <div style={{ position: 'relative' }}>
                  <Lock style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#6b7280' }} size={18} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="input"
                    style={{ paddingLeft: 36, paddingRight: 36, background: '#fff', borderColor: '#e5e7eb', color: '#111' }}
                    placeholder="Enter your password"
                    required
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)' }}>
                    {showPassword ? <EyeOff size={18} color="#6b7280" /> : <Eye size={18} color="#6b7280" />}
                  </button>
                </div>
              </div>

              {!isLogin && (
                <div>
                  <label className="small" style={{ color: '#374151' }}>Confirm Password</label>
                  <div style={{ position: 'relative' }}>
                    <Lock style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#6b7280' }} size={18} />
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      className="input"
                      style={{ paddingLeft: 36, paddingRight: 36, background: '#fff', borderColor: '#e5e7eb', color: '#111' }}
                      placeholder="Confirm your password"
                    />
                    <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)' }}>
                      {showConfirmPassword ? <EyeOff size={18} color="#6b7280" /> : <Eye size={18} color="#6b7280" />}
                    </button>
                  </div>
                </div>
              )}

              <button className="btn" type="submit" style={{ background: 'linear-gradient(90deg,#7e22ce,#ec4899)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
                <ArrowRight size={16} />
              </button>
            </form>

            <div style={{ marginTop: 12, textAlign: 'center' }}>
              <span className="small" style={{ color: '#6b7280' }}>
                {isLogin ? "Don't have an account? " : 'Already have an account? '}
              </span>
              <button onClick={() => setIsLogin(!isLogin)} className="small" style={{ color: '#7e22ce', marginLeft: 4 }}>
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 