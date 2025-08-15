import { FormEvent, useState } from 'react'
import { createTenant } from '@api/tenant'
import { loginTenant } from '@api/auth'
import { useAuthStore } from '@store/auth'
import { useNavigate } from 'react-router-dom'

export default function Signup() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [phone, setPhone] = useState('')
  const [company, setCompany] = useState('')
  const [slug, setSlug] = useState('')
  const [city, setCity] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setMessage(null); setError(null)
    try {
      await createTenant({
        email,
        first_name: firstName,
        last_name: lastName,
        password,
        phone_no: phone,
        company_name: company,
        slug,
        city,
      })
      // Auto-login then go to dashboard
      const data = await loginTenant(email, password)
      useAuthStore.getState().login({ token: data.access_token })
      navigate('/tenant')
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to create account')
    }
  }

  const handleBackToLogin = () => {
    navigate('/login')
  }

  return (
    <main className="bw" aria-label="Create account">
      <div className="bw-container bw-auth">
        <div className="bw-auth-card bw-card" role="form" aria-labelledby="signup-title">
          <h1 id="signup-title" style={{ margin: 0, fontSize: 28 }}>Create account</h1>
          <p className="small-muted" style={{ marginTop: 6 }}>Set up your company profile in minutes.</p>

          <form onSubmit={submit} className="vstack" style={{ display: 'grid', gap: 12, marginTop: 16 }}>
            <div style={{ display: 'grid', gap: 12, gridTemplateColumns: '1fr' }}>
              <label className="small-muted">First name
                <input className="bw-input" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
              </label>
              <label className="small-muted">Last name
                <input className="bw-input" value={lastName} onChange={(e) => setLastName(e.target.value)} />
              </label>
            </div>

            <div style={{ display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr' }}>
              <label className="small-muted">Email
                <input className="bw-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </label>
              <label className="small-muted">Password
                <input className="bw-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              </label>
            </div>

            <label className="small-muted">Phone
              <input className="bw-input" placeholder="+1 555-555-5555" value={phone} onChange={(e) => setPhone(e.target.value)} />
            </label>

            <div style={{ display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr' }}>
              <label className="small-muted">Company
                <input className="bw-input" value={company} onChange={(e) => setCompany(e.target.value)} />
              </label>
              <label className="small-muted">Slug
                <input className="bw-input" placeholder="my-company" value={slug} onChange={(e) => setSlug(e.target.value)} />
              </label>
              <label className="small-muted">City
                <input className="bw-input" value={city} onChange={(e) => setCity(e.target.value)} />
              </label>
            </div>

            {error && <div className="small-muted" style={{ color: '#ffb3b3' }}>{error}</div>}
            {message && <div className="small-muted" style={{ color: '#b3ffcb' }}>{message}</div>}

            <button className="bw-btn" type="submit" style={{ color: '#000' }}>Create account</button>

            <div style={{ marginTop: 12, textAlign: 'center' }}>
              <span className="small-muted">Already have an account? </span>
              <button 
                type="button" 
                className="bw-btn-outline" 
                style={{ padding: '4px 8px', marginLeft: 6 }} 
                onClick={handleBackToLogin}
              >
                Sign in
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
} 