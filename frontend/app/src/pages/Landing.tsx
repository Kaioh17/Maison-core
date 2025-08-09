import Header from '@components/Header'
import { Link } from 'react-router-dom'
import { Car, Users, Building2, Plane, Clock3, MapPin, ShieldCheck, Sparkles } from 'lucide-react'

const NAMES = [
  'Ava', 'Noah', 'Isabella', 'Liam', 'Sophia', 'Mason', 'Emma', 'Oliver', 'Mia', 'Ethan',
  'Charlotte', 'James', 'Amelia', 'Benjamin', 'Harper', 'Elijah', 'Evelyn', 'Lucas', 'Abigail', 'Henry'
]

export default function Landing() {
  return (
    <div className="container" style={{ position: 'relative' }}>
      {/* subtle background names */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', opacity: 0.05, overflow: 'hidden' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 24, padding: 24 }}>
          {NAMES.map((n, i) => (
            <div key={i} style={{
              border: '1px solid rgba(212,175,55,0.25)',
              borderRadius: 12,
              padding: '8px 12px',
              textAlign: 'center',
              color: '#d4af37',
              whiteSpace: 'nowrap',
            }}>{n}</div>
          ))}
        </div>
      </div>

      <Header />

      <div className="hero" style={{ position: 'relative' }}>
        <span className="badge">Where luxury meets technology</span>
        <h1>Transform Your Luxury Transportation Business with Maison</h1>
        <p style={{ marginTop: 8 }}>
          The complete platform built for premium car service companies. Scale your luxury transportation empire with
          enterprise‑grade technology that grows with your business.
        </p>
        <div className="hstack" style={{ marginTop: 16 }}>
          <Link to="/login" className="btn">Login</Link>
          <Link to="/signup" className="btn secondary">Create Account</Link>
        </div>
      </div>

      {/* Why Industry Leaders Choose Maison */}
      <div className="grid" style={{ marginTop: 24 }}>
        <div className="grid-12">
          <div className="card">
            <h2 className="hstack" style={{ gap: 8 }}><Sparkles /> Why Industry Leaders Choose Maison</h2>
            <div className="grid" style={{ marginTop: 12 }}>
              <div className="grid-6">
                <div className="section">
                  <h3>Multi‑Tenant Mastery</h3>
                  <p className="small">
                    Built from the ground up for transportation companies managing multiple brands, fleets, and markets.
                    One platform, unlimited possibilities.
                  </p>
                </div>
                <div className="section" style={{ marginTop: 12 }}>
                  <h3>Three Perfect Portals</h3>
                  <ul className="small">
                    <li className="hstack" style={{ gap: 8 }}><Building2 /> Command Center for company administrators</li>
                    <li className="hstack" style={{ gap: 8 }}><Users /> Driver Hub for your professional chauffeurs</li>
                    <li className="hstack" style={{ gap: 8 }}><ShieldCheck /> Premium Experience for your discerning clientele</li>
                  </ul>
                </div>
              </div>
              <div className="grid-6">
                <div className="section">
                  <h3>Smart Service Types</h3>
                  <ul className="small">
                    <li className="hstack" style={{ gap: 8 }}><Plane /> Airport Transfers with automated city‑airport mapping</li>
                    <li className="hstack" style={{ gap: 8 }}><Clock3 /> Hourly Services for executive travel and events</li>
                    <li className="hstack" style={{ gap: 8 }}><MapPin /> Point‑to‑Point luxury transportation</li>
                  </ul>
                </div>
                <div className="section" style={{ marginTop: 12 }}>
                  <h3>Fleet & Security</h3>
                  <div className="hstack" style={{ gap: 16 }}>
                    <span className="badge"><Car /> Fleet Management</span>
                    <span className="badge"><ShieldCheck /> JWT Auth</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dummy visual panels */}
      <div className="grid" style={{ marginTop: 24 }}>
        <div className="grid-6">
          <div className="card">
            <h3>Fleet Intelligence</h3>
            <p className="small">Advanced vehicle management with real‑time tracking, maintenance scheduling, and performance analytics.</p>
            <div className="mock-img">Luxury Fleet</div>
          </div>
        </div>
        <div className="grid-6">
          <div className="card">
            <h3>Seamless Booking Engine</h3>
            <p className="small">Sophisticated reservation system for complex itineraries, recurring trips, and last‑minute changes.</p>
            <div className="mock-img">Executive Transfers</div>
          </div>
        </div>
        <div className="grid-6">
          <div className="card">
            <h3>Driver Excellence Program</h3>
            <p className="small">Comprehensive onboarding, performance tracking, and QA for in‑house and partner drivers.</p>
            <div className="mock-img">Chauffeur Hub</div>
          </div>
        </div>
        <div className="grid-6">
          <div className="card">
            <h3>Real‑Time Operations</h3>
            <p className="small">Live booking management, dispatch, and customer communications that keep business moving.</p>
            <div className="mock-img">Control Center</div>
          </div>
        </div>
      </div>

      {/* Built for scale */}
      <div className="card" style={{ marginTop: 24 }}>
        <h2>Built for Scale, Designed for Luxury</h2>
        <p className="small">
          Whether you're managing a boutique fleet or a multi‑city operation, Maison adapts to your ambitions. Our modern API architecture
          ensures lightning‑fast performance while our intuitive interfaces keep your team productive.
        </p>
        <div className="hstack" style={{ marginTop: 12 }}>
          <Link to="/signup" className="btn">Get Started</Link>
          <Link to="/login" className="btn secondary">Login</Link>
        </div>
      </div>

    </div>
  )
} 