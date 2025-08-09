import { FormEvent, useState } from 'react'
import { createTenant } from '@api/tenant'

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
      setMessage('Account created. You can sign in now.')
      setEmail(''); setPassword(''); setFirstName(''); setLastName(''); setPhone(''); setCompany(''); setSlug(''); setCity('')
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to create account')
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h2>Create Account</h2>
        <form onSubmit={submit} className="vstack">
          <div className="grid">
            <div className="grid-6">
              <label>First name</label>
              <input className="input" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            </div>
            <div className="grid-6">
              <label>Last name</label>
              <input className="input" value={lastName} onChange={(e) => setLastName(e.target.value)} />
            </div>
          </div>
          <div className="grid">
            <div className="grid-6">
              <label>Email</label>
              <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div className="grid-6">
              <label>Password</label>
              <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
          </div>
          <div>
            <label>Phone</label>
            <input className="input" placeholder="+1 555-555-5555" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
          <div className="grid">
            <div className="grid-6">
              <label>Company</label>
              <input className="input" value={company} onChange={(e) => setCompany(e.target.value)} />
            </div>
            <div className="grid-6">
              <label>Slug</label>
              <input className="input" placeholder="my-company" value={slug} onChange={(e) => setSlug(e.target.value)} />
            </div>
            <div className="grid-6">
              <label>City</label>
              <input className="input" value={city} onChange={(e) => setCity(e.target.value)} />
            </div>
          </div>

          {error && <div className="small" style={{ color: '#f87171' }}>{error}</div>}
          {message && <div className="small" style={{ color: '#10b981' }}>{message}</div>}
          <div className="hstack">
            <button className="btn" type="submit">Create account</button>
          </div>
        </form>
      </div>
    </div>
  )
} 