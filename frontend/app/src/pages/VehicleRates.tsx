import { useEffect, useState } from 'react'
import { getVehicleRates, setVehicleRates } from '@api/vehicles'

export default function VehicleRates() {
  const [rates, setRates] = useState<any[]>([])
  const [form, setForm] = useState({ vehicle_category: '', vehicle_flat_rate: '' })

  const load = async () => {
    const data = await getVehicleRates()
    setRates(data)
  }

  useEffect(() => {
    load()
  }, [])

  const submit = async () => {
    if (!form.vehicle_category || !form.vehicle_flat_rate) return
    await setVehicleRates({ vehicle_category: form.vehicle_category, vehicle_flat_rate: Number(form.vehicle_flat_rate) })
    setForm({ vehicle_category: '', vehicle_flat_rate: '' })
    await load()
  }

  return (
    <div className="container">
      <div className="card">
        <h3>Vehicle Rates</h3>
        <ul>
          {rates.map((r) => (
            <li key={r.id}>{r.vehicle_category}: {r.vehicle_flat_rate}</li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h3>Set Rate</h3>
        <div className="row">
          <input className="input" placeholder="Vehicle Category" value={form.vehicle_category} onChange={(e) => setForm({ ...form, vehicle_category: e.target.value })} />
          <input className="input" placeholder="Flat Rate" value={form.vehicle_flat_rate} onChange={(e) => setForm({ ...form, vehicle_flat_rate: e.target.value })} />
          <button className="btn" onClick={submit}>Save</button>
        </div>
      </div>
    </div>
  )
} 