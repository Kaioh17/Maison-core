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
          <Link to="/signup" className="bw-btn" aria-label="Get started" style={{ color: '#fafafaff' }}>Get started</Link>
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
        <h1 id="hero-title" className="bw-h1">Run Your Fleet. Your Brand. Your Way.</h1>
        <p className="bw-sub">Run your limo business your way — bookings, drivers, payments, and branding all in one simple, scalable platform.</p>
        <div className="hstack" style={{ display: 'flex', gap: 12 }}>
          <Link to="/signup" className="bw-btn" style={{ color: '#ffffffff' }}>Get started</Link>
          <a href="#demo" className="bw-btn-outline" aria-label="See demo">See demo</a>
        </div>
      </div>
      <div className="bw-hero-art" aria-hidden="true">
        <img 
          src="/images/hero-luxury-car.jpg" 
          alt="Professional chauffeur in black suit standing next to sleek black luxury sedan" 
          style={{ 
            width: '100%', 
            height: '100%', 
            objectFit: 'cover', 
            borderRadius: '8px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
          }}
        />
      </div>
    </section>
  )
}

function Features() {
  const items = [
    { title: 'Easy company registration', desc: 'Get your ride-sharing business up and running quickly with streamlined onboarding.', link: '#' },
    { title: 'Register vehicles & drivers', desc: 'Add your fleet and team members with just one click for efficient management.', link: '#' },
    { title: 'Flexible pricing setup', desc: 'Configure pricing models including per hour, per mile, base fares, and more.', link: '#' },
    { title: 'Custom branded experience', desc: 'Configure your own branded site and booking flow to match your brand.', link: '#' },
    { title: 'Scalable growth plans', desc: 'Upgrade plans as your team grows, from solo driver to growing fleet.', link: '#' },
  ]
  return (
    <section id="product" className="section bw-container" aria-label="Key features">
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h2>Everything You Need. Nothing You Don't</h2>
        <p className="small-muted" style={{ textAlign: 'center', marginBottom: 24, fontSize: '16px' }}>
          Maison scales with you — from solo driver to growing fleet.
        </p>
      </div>
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

function DriverFeatures() {
  const driverFeatures = [
    { 
      title: 'Self-service onboarding', 
      desc: 'Drivers can join via secure links without complex paperwork or waiting for admin approval.',
      icon: '🔗'
    },
    { 
      title: 'Flexible documentation', 
      desc: 'Upload vehicle & document info for outsourced drivers or personal details for in-house teams.',
      icon: '📋'
    },
    { 
      title: 'Real-time tracking', 
      desc: 'Track jobs, pay, and tips in real time for complete transparency and better driver satisfaction.',
      icon: '📱'
    },
    { 
      title: 'Mobile-first design', 
      desc: 'Mobile-friendly access without clunky dispatcher systems - drivers stay connected on the go.',
      icon: '📱'
    },
  ]
  return (
    <section className="section bw-container" aria-label="Driver-friendly features">
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h2>Driver-Friendly From Day One</h2>
        <p className="small-muted" style={{ fontSize: '16px', marginTop: 8 }}>
          Your drivers aren't "assets" — they're users.
        </p>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '48px', marginBottom: '32px' }}>
        <div style={{ flex: 1 }}>
          <img 
            src="/images/driver-experience.jpg" 
            alt="Gloved hand opening luxury car door - representing premium service" 
            style={{ 
              width: '100%', 
              maxWidth: '400px', 
              borderRadius: '8px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
            }}
          />
        </div>
        <div style={{ flex: 1 }}>
          <p style={{ fontSize: '18px', lineHeight: '1.6', color: '#666' }}>
            Experience the difference of a platform designed specifically for luxury transportation professionals. 
            Our driver-focused approach ensures your team has everything they need to deliver exceptional service.
          </p>
        </div>
      </div>
      <div className="bw-grid-3">
        {driverFeatures.map((feature) => (
          <article key={feature.title} className="bw-card" role="article">
            <div style={{ fontSize: '24px', marginBottom: 12 }}>{feature.icon}</div>
            <h3>{feature.title}</h3>
            <p className="small-muted" style={{ marginTop: 6 }}>{feature.desc}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

function BookingExperience() {
  const bookingFeatures = [
    { 
      title: 'Unique booking link', 
      desc: 'Riders book through your branded page — not ours. Unique URL: maison.com/ride/{yourcompany}',
      icon: '🔗'
    },
    { 
      title: 'Your brand, your way', 
      desc: 'See your logo, your prices, your services. Complete white-label experience for your business.',
      icon: '🎨'
    },
    { 
      title: 'Simple 4-step process', 
      desc: 'Select vehicle, set service type, choose pickup/drop-off, confirm & pay. Streamlined for riders.',
      icon: '📋'
    },
    { 
      title: 'Secure payments', 
      desc: 'Cash or card payments with Stripe-secured transactions. Multiple payment options for convenience.',
      icon: '💳'
    },
    { 
      title: 'Automated confirmations & reminders', 
      desc: 'Keep riders informed with automatic booking confirmations, pickup reminders, and status updates.',
      icon: '📱'
    },
  ]
  return (
    <section className="section bw-container" aria-label="Smooth booking experience">
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h2>A Smooth Booking Experience</h2>
        <p className="small-muted" style={{ fontSize: '16px', marginTop: 8 }}>
          Riders book through your branded page — not ours.
        </p>
      </div>
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <img 
          src="/images/booking-experience.jpg" 
          alt="Professional chauffeur holding car door open for passenger with suitcase" 
          style={{ 
            maxWidth: '600px', 
            width: '100%', 
            borderRadius: '8px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
          }}
        />
      </div>
      <div className="bw-grid-3">
        {bookingFeatures.map((feature) => (
          <article key={feature.title} className="bw-card" role="article">
            <div style={{ fontSize: '24px', marginBottom: 12 }}>{feature.icon}</div>
            <h3>{feature.title}</h3>
            <p className="small-muted" style={{ marginTop: 6 }}>{feature.desc}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

function Pricing() {
  const pricingFeatures = [
    { 
      title: 'Flat monthly tenant fee', 
      desc: 'Simple, predictable pricing with no hidden costs or surprise charges.',
      icon: '💰'
    },
    { 
      title: 'Add drivers as you grow', 
      desc: 'Scale your team incrementally. Pay only for what you need, when you need it.',
      icon: '📈'
    },
    { 
      title: 'Optional add-ons', 
      desc: 'Enhance your service with SMS reminders, Stripe deposit verification, and other premium features.',
      icon: '⚡'
    },
    { 
      title: 'Cancel or scale anytime', 
      desc: 'No long-term contracts. Adjust your plan up or down based on your business needs.',
      icon: '🔄'
    },
  ]
  return (
    <section id="pricing" className="section bw-container" aria-label="Pricing">
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h2>Fair, Transparent Pricing</h2>
        <p className="small-muted" style={{ fontSize: '16px', marginTop: 8 }}>
          No contracts. No mystery fees.
        </p>
      </div>
      <div className="bw-grid-3">
        {pricingFeatures.map((feature) => (
          <article key={feature.title} className="bw-card" role="article">
            <div style={{ fontSize: '24px', marginBottom: 12 }}>{feature.icon}</div>
            <h3>{feature.title}</h3>
            <p className="small-muted" style={{ marginTop: 6 }}>{feature.desc}</p>
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

function FinalCTA() {
  return (
    <section className="section bw-container" aria-label="Final call to action">
      <div style={{ 
        textAlign: 'center', 
        maxWidth: '800px', 
        margin: '0 auto',
        position: 'relative',
        zIndex: 2
      }}>
        <h2 style={{ fontSize: '2.5rem', marginBottom: 16 }}>Maison is the Next Generation of Limo Software.</h2>
        <p className="bw-sub" style={{ fontSize: '1.25rem', marginBottom: 32, lineHeight: 1.6 }}>
          Stop fighting with outdated systems. Start running your business on a platform built for you — operators, drivers, and riders.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16 }}>
          <Link to="/signup" className="bw-btn" style={{ color: '#ffffffff', fontSize: '1.1rem', padding: '12px 32px' }}>
            Start Free Today
          </Link>
        </div>
      </div>
      <div style={{ 
        position: 'absolute', 
        top: 0, 
        left: 0, 
        right: 0, 
        bottom: 0, 
        zIndex: 1,
        opacity: 0.1,
        backgroundImage: 'url(/images/final-cta-background.jpg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      }} />
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
          <button className="bw-btn" style={{ marginTop: 8, color: '#ffffffff' }}>Subscribe</button>
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
      <DriverFeatures />
      <BookingExperience />
      <Pricing />
      <Steps />
      <Testimonial />
      <FinalCTA />
      <Footer />
    </main>
  )
}