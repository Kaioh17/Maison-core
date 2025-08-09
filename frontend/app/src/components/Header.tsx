import { Link } from 'react-router-dom'
import { useAuthStore } from '@store/auth'

export default function Header() {
  const { accessToken, logout } = useAuthStore()
  return (
    <div className="header card">
      <div className="brand">Maison</div>
      <nav className="hstack">
        {!accessToken ? (
          <>
            <Link to="/login" className="btn secondary">Login</Link>
            <Link to="/signup" className="btn">Create Account</Link>
          </>
        ) : (
          <button className="btn danger" onClick={logout}>Logout</button>
        )}
      </nav>
    </div>
  )
} 