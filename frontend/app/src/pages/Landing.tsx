import { Link } from 'react-router-dom'

function Header() {
  return (
    <header className="bw-topnav">
      <div className="bw-container bw-topnav-inner" role="navigation" aria-label="Main">
        <div className="bw-brand">Maison</div>
        <nav className="bw-nav">
          <a href="#product">Product</a>
          <a href="#pricing">Pricing</a>
          <a href="#docs">Docs</a>
        </nav>
        <div className="bw-cta">
          <Link to="/login" className="bw-btn-outline" aria-label="Login">Login</Link>
          <Link to="/signup" className="bw-btn" aria-label="Get started" style={{ color: '#000' }}>Get started</Link>
        </div>
        <button className="bw-menu" aria-label="Open menu">≡</button>
      </div>
    </header>
  )
}

function Hero() {
  return (
    <section className="bw-container bw-hero" aria-labelledby="hero-title">
      <div>
        <h1 id="hero-title" className="bw-h1">Build. Ship. Iterate.</h1>
        <p className="bw-sub">A clean platform that helps teams move from idea to product faster.</p>
        <div className="hstack" style={{ display: 'flex', gap: 12 }}>
          <Link to="/signup" className="bw-btn" style={{ color: '#000' }}>Get started</Link>
          <a href="#demo" className="bw-btn-outline" aria-label="See demo">See demo</a>
        </div>
      </div>
      <div className="bw-hero-art" aria-hidden="true">abstract · 1px</div>
    </section>
  )
}

function Features() {
  const items = [
    { title: 'Fast setup', desc: 'Spin up projects quickly with sensible defaults and tooling.', link: '#' },
    { title: 'Collaborative', desc: 'Work together with clear roles, reviews and streamlined handoffs.', link: '#' },
    { title: 'Secure by default', desc: 'Privacy-first architecture with hardened, least-privilege access.', link: '#' },
  ]
  return (
    <section id="product" className="section bw-container" aria-label="Key features">
      <h2>Key features</h2>
      <div className="bw-grid-3">
        {items.map((it) => (
          <article key={it.title} className="bw-card" role="article">
            <h3>{it.title}</h3>
            <p className="small-muted" style={{ marginTop: 6 }}>{it.desc}</p>
            <a href={it.link} className="small-muted" style={{ marginTop: 10, display: 'inline-block' }} aria-label={`${it.title} — learn more`}>
              Learn more
            </a>
          </article>
        ))}
      </div>
    </section>
  )
}

function Steps() {
  const steps = [
    { n: 1, t: 'Plan', d: 'Outline scope and invite your team.' },
    { n: 2, t: 'Build', d: 'Track progress with structured reviews.' },
    { n: 3, t: 'Ship', d: 'Publish confidently with audit trails.' },
  ]
  return (
    <section className="section bw-container" aria-label="How it works">
      <h2>How it works</h2>
      <div className="bw-grid-3">
        {steps.map((s) => (
          <div key={s.n} className="bw-card" role="group" aria-label={`Step ${s.n}`}>
            <div className="small-muted" style={{ marginBottom: 8 }}>Step {s.n}</div>
            <h3>{s.t}</h3>
            <p className="small-muted" style={{ marginTop: 6 }}>{s.d}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

function Testimonial() {
  return (
    <section className="section bw-container" aria-label="Testimonial">
      <blockquote className="bw-card" style={{ textAlign: 'center' }}>
        <p style={{ margin: 0 }}>
          “Clean, focused and predictable. We move from idea to release without distractions.”
        </p>
        <footer className="small-muted" style={{ marginTop: 8 }}>Alex M. · Product Lead</footer>
      </blockquote>
    </section>
  )
}

function Footer() {
  return (
    <footer className="bw-footer" role="contentinfo">
      <div className="bw-container bw-footer-grid">
        <div>
          <div className="bw-brand">Maison</div>
          <p className="small-muted" style={{ marginTop: 8 }}>Minimal platform to build, ship and iterate faster.</p>
        </div>
        <nav aria-label="Footer Product">
          <h3>Product</h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: '8px 0 0 0' }}>
            <li><a href="#product">Overview</a></li>
            <li><a href="#docs">Docs</a></li>
            <li><a href="#pricing">Pricing</a></li>
          </ul>
        </nav>
        <nav aria-label="Footer Company">
          <h3>Company</h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: '8px 0 0 0' }}>
            <li><a href="#about">About</a></li>
            <li><a href="#blog">Blog</a></li>
            <li><a href="#contact">Contact</a></li>
          </ul>
        </nav>
        <form aria-label="Newsletter signup" onSubmit={(e) => e.preventDefault()}>
          <h3>Newsletter</h3>
          <label className="small-muted" htmlFor="email" style={{ display: 'block', marginTop: 8 }}>Email</label>
          <input id="email" className="bw-input" type="email" placeholder="you@email" aria-required="true" />
          <button className="bw-btn" style={{ marginTop: 8, color: '#000' }}>Subscribe</button>
        </form>
      </div>
      <div className="bw-container" style={{ marginTop: 16 }}>
        <div className="small-muted">© {new Date().getFullYear()} Maison. All rights reserved.</div>
      </div>
    </footer>
  )
}

export default function Landing() {
  return (
    <main className="bw" aria-label="Landing">
      <Header />
      <Hero />
      <Features />
      <Steps />
      <Testimonial />
      <Footer />
    </main>
  )
}