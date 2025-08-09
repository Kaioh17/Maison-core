import { useState } from 'react'
import { updateTenantSettings } from '@api/tenantSettings'

export default function TenantSettings() {
  const [form, setForm] = useState({
    theme: 'light',
    logo_url: '',
    slug: '',
    enable_branding: true,
    base_fare: 3,
    per_minute_rate: 0.5,
    per_mile_rate: 1.5,
    per_hour_rate: 25,
    rider_tiers_enabled: false,
    cancellation_fee: 5,
    discounts: false,
  })
  const [message, setMessage] = useState('')

  const save = async () => {
    await updateTenantSettings(form)
    setMessage('Settings saved')
    setTimeout(() => setMessage(''), 1500)
  }

  return (
    <div className="container">
      <div className="card">
        <h3>Tenant Settings</h3>
        <div className="grid">
          <div className="grid-6">
            <label>Theme</label>
            <select className="input" value={form.theme} onChange={(e) => setForm({ ...form, theme: e.target.value })}>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>
          <div className="grid-6">
            <label>Logo URL</label>
            <input className="input" value={form.logo_url} onChange={(e) => setForm({ ...form, logo_url: e.target.value })} />
          </div>
          <div className="grid-6">
            <label>Slug</label>
            <input className="input" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} />
          </div>
          <div className="grid-6">
            <label>Branding Enabled</label>
            <select className="input" value={String(form.enable_branding)} onChange={(e) => setForm({ ...form, enable_branding: e.target.value === 'true' })}>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>
          <div className="grid-6">
            <label>Base Fare</label>
            <input className="input" value={form.base_fare} onChange={(e) => setForm({ ...form, base_fare: Number(e.target.value) })} />
          </div>
          <div className="grid-6">
            <label>Per Minute Rate</label>
            <input className="input" value={form.per_minute_rate} onChange={(e) => setForm({ ...form, per_minute_rate: Number(e.target.value) })} />
          </div>
          <div className="grid-6">
            <label>Per Mile Rate</label>
            <input className="input" value={form.per_mile_rate} onChange={(e) => setForm({ ...form, per_mile_rate: Number(e.target.value) })} />
          </div>
          <div className="grid-6">
            <label>Per Hour Rate</label>
            <input className="input" value={form.per_hour_rate} onChange={(e) => setForm({ ...form, per_hour_rate: Number(e.target.value) })} />
          </div>
          <div className="grid-6">
            <label>Rider Tiers Enabled</label>
            <select className="input" value={String(form.rider_tiers_enabled)} onChange={(e) => setForm({ ...form, rider_tiers_enabled: e.target.value === 'true' })}>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>
          <div className="grid-6">
            <label>Cancellation Fee</label>
            <input className="input" value={form.cancellation_fee} onChange={(e) => setForm({ ...form, cancellation_fee: Number(e.target.value) })} />
          </div>
          <div className="grid-6">
            <label>Discounts Enabled</label>
            <select className="input" value={String(form.discounts)} onChange={(e) => setForm({ ...form, discounts: e.target.value === 'true' })}>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>
        </div>
        <div className="hstack" style={{ marginTop: 12 }}>
          <button className="btn" onClick={save}>Save</button>
        </div>
        {message && <div className="small">{message}</div>}
      </div>
    </div>
  )
} 