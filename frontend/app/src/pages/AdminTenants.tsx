import { useEffect, useState } from 'react'
import { getAllTenants, deleteTenant } from '@api/admin'
import { useAuthStore } from '@store/auth'

export default function AdminTenants() {
  const [tenants, setTenants] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await getAllTenants()
      setTenants(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const del = async (id: number) => {
    await deleteTenant(id)
    await load()
  }

  return (
    <div className="container">
      <div className="hstack" style={{ justifyContent: 'space-between' }}>
        <h2>Admin - Tenants</h2>
        <button className="btn" onClick={() => useAuthStore.getState().logout()}>Logout</button>
      </div>

      <div className="card">
        {loading ? 'Loading...' : (
          <table className="small" style={{ width: '100%' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>ID</th>
                <th style={{ textAlign: 'left' }}>Company</th>
                <th style={{ textAlign: 'left' }}>Email</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((t) => (
                <tr key={t.id}>
                  <td>{t.id}</td>
                  <td>{t.company_name}</td>
                  <td>{t.email}</td>
                  <td>
                    <button className="btn danger" onClick={() => del(t.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
} 