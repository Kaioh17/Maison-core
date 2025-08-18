import { Link } from 'react-router-dom'
import './landing.css'
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
          src="/src/images/hero-luxury-car.jpg" 
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
    { title: 'Easy company registration', desc: 'Get your ride-sharing business up and running quickly with streamlined onboarding.', link: '#', icon: '🏢' },
    { title: 'Register vehicles & drivers', desc: 'Add your fleet and team members with just one click for efficient management.', link: '#', icon: '🚗' },
    { title: 'Flexible pricing setup', desc: 'Configure pricing models including per hour, per mile, base fares, and more.', link: '#', icon: '💰' },
    { title: 'Custom branded experience', desc: 'Configure your own branded site and booking flow to match your brand.', link: '#', icon: '🎨' },
    { title: 'Scalable growth plans', desc: 'Upgrade plans as your team grows, from solo driver to growing fleet.', link: '#', icon: '📈' },
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
            <div style={{ 
              width: '32px', 
              height: '32px', 
              marginBottom: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                {it.title === 'Easy company registration' && (
                  <path d="M3 21h18M9 7h6M9 11h6M9 15h6M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/>
                )}
                {it.title === 'Register vehicles & drivers' && (
                  <>
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                    <circle cx="9" cy="10" r="2"/>
                    <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
                  </>
                )}
                {it.title === 'Flexible pricing setup' && (
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                )}
                {it.title === 'Custom branded experience' && (
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                )}
                {it.title === 'Scalable growth plans' && (
                  <path d="M3 3v18h18M8 12l3 3 5-5"/>
                )}
              </svg>
            </div>
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
      icon: 'link'
    },
    { 
      title: 'Flexible documentation', 
      desc: 'Upload vehicle & document info for outsourced drivers or personal details for in-house teams.',
      icon: 'document'
    },
    { 
      title: 'Real-time tracking', 
      desc: 'Track jobs, pay, and tips in real time for complete transparency and better driver satisfaction.',
      icon: 'tracking'
    },
    { 
      title: 'Mobile-first design', 
      desc: 'Mobile-friendly access without clunky dispatcher systems - drivers stay connected on the go.',
      icon: 'mobile'
    },
  ]
  
  const getIcon = (iconType: string) => {
    switch (iconType) {
      case 'link':
        return <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>;
      case 'document':
        return <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>;
      case 'tracking':
        return <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>;
      case 'mobile':
        return <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>;
      default:
        return <circle cx="12" cy="12" r="10"/>;
    }
  };

  return (
    <section className="section bw-container" aria-label="Driver-friendly features">
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h2>Driver-Friendly From Day One</h2>
        <p className="small-muted" style={{ fontSize: '16px', marginTop: 8 }}>
          Your drivers aren't "assets" — they're users.
        </p>
      </div>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: '64px', 
        alignItems: 'center', 
        marginBottom: '48px',
        padding: '32px 0'
      }}>
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          justifyContent: 'center',
          gap: '24px'
        }}>
          <h3 style={{ 
            fontSize: '24px', 
            marginBottom: '16px', 
            color: '#333',
            fontWeight: '600'
          }}>
            Built for Professional Excellence
          </h3>
          <p style={{ 
            fontSize: '18px', 
            lineHeight: '1.7', 
            color: '#555',
            marginBottom: '16px'
          }}>
            Experience the difference of a platform designed specifically for luxury transportation professionals. 
            Our driver-focused approach ensures your team has everything they need to deliver exceptional service.
          </p>
          <p style={{ 
            fontSize: '16px', 
            lineHeight: '1.6', 
            color: '#666',
            fontStyle: 'italic'
          }}>
            From seamless onboarding to real-time operations, every feature is crafted with your drivers' success in mind.
          </p>
        </div>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <img 
            src="/src/images/driver-experience.jpeg" 
            alt="Gloved hand opening luxury car door - representing premium service" 
            style={{ 
              width: '100%', 
              maxWidth: '500px', 
              borderRadius: '12px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
              transition: 'transform 0.3s ease, box-shadow 0.3s ease'
            }}
            onMouseEnter={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.transform = 'scale(1.02)';
              target.style.boxShadow = '0 12px 40px rgba(0,0,0,0.2)';
            }}
            onMouseLeave={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.transform = 'scale(1)';
              target.style.boxShadow = '0 8px 32px rgba(0,0,0,0.15)';
            }}
          />
        </div>
      </div>
      <div className="bw-grid-3">
        {driverFeatures.map((feature) => (
          <article key={feature.title} className="bw-card" role="article">
            <div style={{ 
              width: '32px', 
              height: '32px', 
              marginBottom: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#000'
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                {getIcon(feature.icon)}
              </svg>
            </div>
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
      icon: 'link'
    },
    { 
      title: 'Your brand, your way', 
      desc: 'See your logo, your prices, your services. Complete white-label experience for your business.',
      icon: 'brand'
    },
    { 
      title: 'Simple 4-step process', 
      desc: 'Select vehicle, set service type, choose pickup/drop-off, confirm & pay. Streamlined for riders.',
      icon: 'process'
    },
    { 
      title: 'Secure payments', 
      desc: 'Cash or card payments with Stripe-secured transactions. Multiple payment options for convenience.',
      icon: 'payment'
    },
    { 
      title: 'Automated confirmations & reminders', 
      desc: 'Keep riders informed with automatic booking confirmations, pickup reminders, and status updates.',
      icon: 'notification'
    },
  ]
  
  const getIcon = (iconType: string) => {
    switch (iconType) {
      case 'link':
        return <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>;
      case 'brand':
        return <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>;
      case 'process':
        return <path d="M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>;
      case 'payment':
        return <><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></>;
      case 'notification':
        return <><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></>;
      default:
        return <circle cx="12" cy="12" r="10"/>;
    }
  };

  return (
    <section className="section bw-container" aria-label="Smooth booking experience">
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h2>A Smooth Booking Experience</h2>
        <p className="small-muted" style={{ fontSize: '16px', marginTop: 8 }}>
          Riders book through your branded page — not ours.
        </p>
      </div>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: '64px', 
        alignItems: 'center', 
        marginBottom: '48px',
        padding: '32px 0'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <img 
            src="src/images/riders-luggage.jpg" 
            alt="Professional chauffeur holding car door open for passenger with suitcase" 
            style={{ 
              width: '100%', 
              maxWidth: '400px', 
              maxHeight: '400px', 
              borderRadius: '12px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
              transition: 'transform 0.3s ease, box-shadow 0.3s ease'
            }}
            onMouseEnter={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.transform = 'scale(1.02)';
              target.style.boxShadow = '0 12px 40px rgba(0,0,0,0.2)';
            }}
            onMouseLeave={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.transform = 'scale(1)';
              target.style.boxShadow = '0 8px 32px rgba(0,0,0,0.15)';
            }}
          />
        </div>
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          justifyContent: 'center',
          gap: '24px'
        }}>
          <h3 style={{ 
            fontSize: '24px', 
            marginBottom: '16px', 
            color: '#333',
            fontWeight: '600'
          }}>
            Seamless Rider Experience
          </h3>
          <p style={{ 
            fontSize: '18px', 
            lineHeight: '1.7', 
            color: '#555',
            marginBottom: '16px'
          }}>
            Create a booking experience that reflects your brand's excellence. Every touchpoint is designed to 
            make riders feel confident and comfortable choosing your service.
          </p>
          <p style={{ 
            fontSize: '16px', 
            lineHeight: '1.6', 
            color: '#666',
            fontStyle: 'italic'
          }}>
            From the first click to the final ride, your riders enjoy a premium, branded experience that builds loyalty.
          </p>
        </div>
      </div>
      <div className="bw-grid-3">
        {bookingFeatures.map((feature) => (
          <article key={feature.title} className="bw-card" role="article">
            <div style={{ 
              width: '32px', 
              height: '32px', 
              marginBottom: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#000'
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                {getIcon(feature.icon)}
              </svg>
            </div>
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
      icon: 'flat-fee'
    },
    { 
      title: 'Add drivers as you grow', 
      desc: 'Scale your team incrementally. Pay only for what you need, when you need it.',
      icon: 'growth'
    },
    { 
      title: 'Optional add-ons', 
      desc: 'Enhance your service with SMS reminders, Stripe deposit verification, and other premium features.',
      icon: 'addons'
    },
    { 
      title: 'Cancel or scale anytime', 
      desc: 'No long-term contracts. Adjust your plan up or down based on your business needs.',
      icon: 'flexibility'
    },
  ]
  
  const getIcon = (iconType: string) => {
    switch (iconType) {
      case 'flat-fee':
        return <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>;
      case 'growth':
        return <path d="M3 3v18h18M8 12l3 3 5-5"/>;
      case 'addons':
        return <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>;
      case 'flexibility':
        return <><path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0"/><path d="M12 7v5l3 3"/></>;
      default:
        return <circle cx="12" cy="12" r="10"/>;
    }
  };

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
            <div style={{ 
              width: '32px', 
              height: '32px', 
              marginBottom: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#000'
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                {getIcon(feature.icon)}
              </svg>
            </div>
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
    <section className="section bw-container" aria-label="Final call to action" style={{
      backgroundColor: '#ffffffff',
      color: '#ffffffff',
      position: 'relative',
      borderRadius: '12px',
      margin: '32px auto',
      padding: '48px 24px',
      maxWidth: '1000px',
      textAlign: 'center'
    }}>
      <div style={{ 
        position: 'relative',
        zIndex: 2
      }}>
        <h2 style={{ fontSize: '2.5rem', marginBottom: 16, color: '#ffffff' }}>Maison is the Next Generation of Limo Software.</h2>
        <p className="bw-sub" style={{ fontSize: '1.25rem', marginBottom: 32, lineHeight: 1.6, color: '#e5e7eb' }}>
          Stop fighting with outdated systems. Start running your business on a platform built for you — operators, drivers, and riders.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16 }}>
          <Link to="/signup" className="bw-btn" style={{ 
            color: '#ffffff', 
            fontSize: '1.1rem', 
            padding: '12px 32px',
            backgroundColor: '#3b82f6',
            borderColor: '#3b82f6'
          }}>
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
        backgroundRepeat: 'no-repeat',
        borderRadius: '12px'
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
    <main className="bw landing-page" aria-label="Landing">
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