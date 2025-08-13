import { Link, NavLink } from 'react-router-dom'

export default function TopNav() {
  return (
    <header className="topnav">
      <div className="brand">Maison</div>
      <nav className="links">
        <NavLink to="/" className={({isActive}) => isActive ? 'active' : ''}>Home</NavLink>
        <a href="#services">Services</a>
        <a href="#story">About</a>
        <a href="#blog">Blog</a>
        <a href="#contact">Contact</a>
      </nav>
      <div className="cta">
        <Link to="/login" className="btn ghost">Login</Link>
        <Link to="/signup" className="btn">Sign up</Link>
      </div>
    </header>
  )
} 