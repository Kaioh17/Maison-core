import { useEffect, useState } from 'react'
import { createBooking, getMyBookings } from '@api/bookings'
import { useAuthStore } from '@store/auth'

export default function RiderDashboard() {
  const [form, setForm] = useState({
    city: '',
    service_type: 'dropoff' as 'airport' | 'hourly' | 'dropoff',
    pickup_location: '',
    dropoff_location: '',
    pickup_time_local: '',
    payment_method: 'cash' as 'cash' | 'card' | 'zelle',
    notes: ''
  })
  const [bookings, setBookings] = useState<any[]>([])

  const load = async () => {
    const b = await getMyBookings()
    setBookings(b)
  }

  useEffect(() => {
    load()
  }, [])

  const book = async () => {
    if (!form.pickup_location || !form.dropoff_location || !form.city || !form.pickup_time_local) return
    await createBooking({
      city: form.city,
      service_type: form.service_type,
      pickup_location: form.pickup_location,
      pickup_time: new Date(form.pickup_time_local).toISOString(),
      dropoff_location: form.dropoff_location,
      payment_method: form.payment_method,
      notes: form.notes || undefined,
    })
    setForm({ city: '', service_type: 'dropoff', pickup_location: '', dropoff_location: '', pickup_time_local: '', payment_method: 'cash', notes: '' })
    await load()
  }

  return (
    <div className="container">
      <div className="hstack" style={{ justifyContent: 'space-between' }}>
        <h2>Rider Dashboard</h2>
        <button className="btn" onClick={() => useAuthStore.getState().logout()}>Logout</button>
      </div>

      <div className="card">
        <h3>Book a Ride</h3>
        <div className="row">
          <input className="input" placeholder="City" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
          <select className="input" value={form.service_type} onChange={(e) => setForm({ ...form, service_type: e.target.value as any })}>
            <option value="dropoff">Dropoff</option>
            <option value="airport">Airport</option>
            <option value="hourly">Hourly</option>
          </select>
          <select className="input" value={form.payment_method} onChange={(e) => setForm({ ...form, payment_method: e.target.value as any })}>
            <option value="cash">Cash</option>
            <option value="card">Card</option>
            <option value="zelle">Zelle</option>
          </select>
        </div>
        <div className="row">
          <input className="input" placeholder="Pickup" value={form.pickup_location} onChange={(e) => setForm({ ...form, pickup_location: e.target.value })} />
          <input className="input" placeholder="Dropoff" value={form.dropoff_location} onChange={(e) => setForm({ ...form, dropoff_location: e.target.value })} />
          <input className="input" type="datetime-local" value={form.pickup_time_local} onChange={(e) => setForm({ ...form, pickup_time_local: e.target.value })} />
          <button className="btn" onClick={book}>Book</button>
        </div>
      </div>

      <div className="card">
        <h3>My Bookings</h3>
        <ul>
          {bookings.map((b) => (
            <li key={b.id}>#{b.id} {b.pickup_location} → {b.dropoff_location} ({b.booking_status})</li>
          ))}
        </ul>
      </div>
    </div>
  )
} 