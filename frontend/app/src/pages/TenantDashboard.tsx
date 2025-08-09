import { useEffect, useState } from 'react'
import { getTenantInfo, getTenantDrivers, getTenantVehicles, getTenantBookings, onboardDriver, assignDriverToVehicle } from '@api/tenant'
import { useAuthStore } from '@store/auth'

export default function TenantDashboard() {
  const [info, setInfo] = useState<any>(null)
  const [drivers, setDrivers] = useState<any[]>([])
  const [vehicles, setVehicles] = useState<any[]>([])
  const [bookings, setBookings] = useState<any[]>([])
  const [newDriver, setNewDriver] = useState({ first_name: '', last_name: '', email: '', driver_type: 'outsourced' })
  const [assign, setAssign] = useState({ vehicleId: '', driverId: '' })

  const load = async () => {
    const [i, d, v, b] = await Promise.all([
      getTenantInfo(),
      getTenantDrivers(),
      getTenantVehicles(),
      getTenantBookings(),
    ])
    setInfo(i.data)
    setDrivers(d.data)
    setVehicles(v.data)
    setBookings(b.data)
  }

  useEffect(() => {
    load()
  }, [])

  const createDriver = async () => {
    if (!newDriver.email || !newDriver.first_name || !newDriver.last_name) return
    await onboardDriver({ ...newDriver, driver_type: newDriver.driver_type as any })
    setNewDriver({ first_name: '', last_name: '', email: '', driver_type: 'outsourced' })
    await load()
  }

  const assignVehicle = async () => {
    const vehicleId = Number(assign.vehicleId)
    const driverId = Number(assign.driverId)
    if (!vehicleId || !driverId) return
    await assignDriverToVehicle(vehicleId, { driver_id: driverId })
    setAssign({ vehicleId: '', driverId: '' })
    await load()
  }

  return (
    <div className="container">
      <div className="hstack" style={{ justifyContent: 'space-between' }}>
        <h2>Tenant Dashboard</h2>
        <button className="btn" onClick={() => useAuthStore.getState().logout()}>Logout</button>
      </div>

      <div className="grid">
        <div className="grid-6">
          <div className="card">
            <h3>Company</h3>
            <pre className="small">{JSON.stringify(info, null, 2)}</pre>
          </div>
          <div className="card">
            <h3>Onboard Driver</h3>
            <div className="row">
              <input className="input" placeholder="First name" value={newDriver.first_name} onChange={(e) => setNewDriver({ ...newDriver, first_name: e.target.value })} />
              <input className="input" placeholder="Last name" value={newDriver.last_name} onChange={(e) => setNewDriver({ ...newDriver, last_name: e.target.value })} />
            </div>
            <div className="row">
              <input className="input" placeholder="Email" value={newDriver.email} onChange={(e) => setNewDriver({ ...newDriver, email: e.target.value })} />
              <select className="input" value={newDriver.driver_type} onChange={(e) => setNewDriver({ ...newDriver, driver_type: e.target.value })}>
                <option value="outsourced">Outsourced</option>
                <option value="in_house">In-house</option>
              </select>
              <button className="btn" onClick={createDriver}>Create</button>
            </div>
          </div>
          <div className="card">
            <h3>Assign Driver to Vehicle</h3>
            <div className="row">
              <select className="input" value={assign.vehicleId} onChange={(e) => setAssign({ ...assign, vehicleId: e.target.value })}>
                <option value="">Select vehicle</option>
                {vehicles.map((v) => (
                  <option key={v.id} value={v.id}>{v.make} {v.model}</option>
                ))}
              </select>
              <select className="input" value={assign.driverId} onChange={(e) => setAssign({ ...assign, driverId: e.target.value })}>
                <option value="">Select driver</option>
                {drivers.map((d) => (
                  <option key={d.id} value={d.id}>{d.first_name} {d.last_name}</option>
                ))}
              </select>
              <button className="btn" onClick={assignVehicle}>Assign</button>
            </div>
          </div>
        </div>
        <div className="grid-6">
          <div className="card">
            <h3>Drivers</h3>
            <ul>
              {drivers.map((d) => (
                <li key={d.id}>{d.first_name} {d.last_name} — {d.email}</li>
              ))}
            </ul>
          </div>
          <div className="card">
            <h3>Vehicles</h3>
            <ul>
              {vehicles.map((v) => (
                <li key={v.id}>{v.make} {v.model}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Bookings</h3>
        <table className="small" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>ID</th>
              <th style={{ textAlign: 'left' }}>Pickup</th>
              <th style={{ textAlign: 'left' }}>Dropoff</th>
              <th style={{ textAlign: 'left' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {bookings.map((b) => (
              <tr key={b.id}>
                <td>{b.id}</td>
                <td>{b.pickup_location}</td>
                <td>{b.dropoff_location}</td>
                <td>{b.booking_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
} 