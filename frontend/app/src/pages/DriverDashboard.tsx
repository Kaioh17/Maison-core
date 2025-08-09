import { useEffect, useState } from 'react'
import { getDriverInfo, getAvailableRides, respondToRide } from '@api/driver'
import { useAuthStore } from '@store/auth'

export default function DriverDashboard() {
  const [info, setInfo] = useState<any>(null)
  const [rides, setRides] = useState<any[]>([])

  const load = async () => {
    const [i, r] = await Promise.all([getDriverInfo(), getAvailableRides()])
    setInfo(i.data)
    setRides(r.data)
  }

  useEffect(() => {
    load()
  }, [])

  const act = async (id: number, action: 'confirm' | 'cancelled') => {
    await respondToRide(id, action)
    await load()
  }

  return (
    <div className="container">
      <div className="hstack" style={{ justifyContent: 'space-between' }}>
        <h2>Driver Dashboard</h2>
        <button className="btn" onClick={() => useAuthStore.getState().logout()}>Logout</button>
      </div>

      <div className="card">
        <h3>My Info</h3>
        <pre className="small">{JSON.stringify(info, null, 2)}</pre>
      </div>

      <div className="card">
        <h3>Available Rides</h3>
        {rides.length === 0 && <div className="small">No rides yet.</div>}
        <ul>
          {rides.map((b) => (
            <li key={b.id} className="hstack" style={{ justifyContent: 'space-between' }}>
              <div>
                #{b.id} {b.pickup_location} → {b.dropoff_location} ({b.status})
              </div>
              <div className="hstack">
                <button className="btn" onClick={() => act(b.id, 'confirm')}>Accept</button>
                <button className="btn danger" onClick={() => act(b.id, 'cancelled')}>Decline</button>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
} 