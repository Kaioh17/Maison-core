import { useState, useEffect } from 'react'
import { getTenantInfo } from '@api/tenant'
import { useAuthStore } from '@store/auth'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Settings, User, Building, MapPin, Phone, Mail, Shield, CreditCard } from 'lucide-react'

export default function TenantSettings() {
  const [info, setInfo] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const loadInfo = async () => {
      try {
        const response = await getTenantInfo()
        setInfo(response.data)
      } catch (error) {
        console.error('Failed to load tenant info:', error)
      } finally {
        setLoading(false)
      }
    }
    loadInfo()
  }, [])

  if (loading) {
    return (
      <div className="bw bw-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div className="bw-loading">Loading settings...</div>
      </div>
    )
  }

  return (
    <div className="bw bw-container" style={{ padding: '24px 0' }}>
      {/* Header */}
      <div className="bw-header" style={{ marginBottom: 32 }}>
        <div className="bw-header-content">
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <button 
              className="bw-btn-outline" 
              onClick={() => navigate('/tenant')}
              style={{ padding: '8px 12px' }}
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </button>
            <h1 style={{ fontSize: 32, margin: 0 }}>Settings</h1>
          </div>
          <div className="bw-header-actions">
            <span className="bw-text-muted">Account Management</span>
            <button 
              className="bw-btn-outline" 
              onClick={() => useAuthStore.getState().logout()}
              style={{ marginLeft: 16 }}
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Settings Sections */}
      <div className="bw-grid" style={{ gap: 24 }}>
        {/* Account Information */}
        <div className="bw-card" style={{ gridColumn: 'span 6' }}>
          <div className="bw-card-header">
            <div className="bw-card-icon">
              <User className="w-5 h-5" />
            </div>
            <h3>Account Information</h3>
          </div>
          <div className="bw-info-grid">
            <div className="bw-info-item">
              <span className="bw-info-label">First Name:</span>
              <span className="bw-info-value">{info?.first_name}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Last Name:</span>
              <span className="bw-info-value">{info?.last_name}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Email:</span>
              <span className="bw-info-value">{info?.email}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Phone:</span>
              <span className="bw-info-value">{info?.phone_no}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Role:</span>
              <span className="bw-info-value">{info?.role}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Member Since:</span>
              <span className="bw-info-value">
                {new Date(info?.created_on).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>

        {/* Company Information */}
        <div className="bw-card" style={{ gridColumn: 'span 6' }}>
          <div className="bw-card-header">
            <div className="bw-card-icon">
              <Building className="w-5 h-5" />
            </div>
            <h3>Company Information</h3>
          </div>
          <div className="bw-info-grid">
            <div className="bw-info-item">
              <span className="bw-info-label">Company Name:</span>
              <span className="bw-info-value">{info?.company_name}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Slug:</span>
              <span className="bw-info-value">{info?.slug}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">City:</span>
              <span className="bw-info-value">{info?.city}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Address:</span>
              <span className="bw-info-value">{info?.address || 'Not provided'}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Verification Status:</span>
              <span className={`bw-info-value ${info?.is_verified ? 'text-green-500' : 'text-yellow-500'}`}>
                {info?.is_verified ? 'Verified' : 'Pending Verification'}
              </span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Account Status:</span>
              <span className={`bw-info-value ${info?.is_active ? 'text-green-500' : 'text-red-500'}`}>
                {info?.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>

        {/* Subscription & Billing */}
        <div className="bw-card" style={{ gridColumn: 'span 6' }}>
          <div className="bw-card-header">
            <div className="bw-card-icon">
              <CreditCard className="w-5 h-5" />
            </div>
            <h3>Subscription & Billing</h3>
          </div>
          <div className="bw-info-grid">
            <div className="bw-info-item">
              <span className="bw-info-label">Subscription Plan:</span>
              <span className="bw-info-value">{info?.subscription_plan || 'No plan'}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Subscription Status:</span>
              <span className="bw-info-value">{info?.subscription_status || 'N/A'}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Stripe Customer ID:</span>
              <span className="bw-info-value">{info?.stripe_customer_id || 'Not connected'}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Stripe Account ID:</span>
              <span className="bw-info-value">{info?.stripe_account_id || 'Not connected'}</span>
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="bw-card" style={{ gridColumn: 'span 6' }}>
          <div className="bw-card-header">
            <div className="bw-card-icon">
              <Settings className="w-5 h-5" />
            </div>
            <h3>Statistics</h3>
          </div>
          <div className="bw-info-grid">
            <div className="bw-info-item">
              <span className="bw-info-label">Total Drivers:</span>
              <span className="bw-info-value">{info?.drivers_count || 0}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Total Rides:</span>
              <span className="bw-info-value">{info?.total_ride_count || 0}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Daily Rides:</span>
              <span className="bw-info-value">{info?.daily_ride_count || 0}</span>
            </div>
            <div className="bw-info-item">
              <span className="bw-info-label">Last Reset:</span>
              <span className="bw-info-value">
                {info?.last_ride_count_reset ? new Date(info.last_ride_count_reset).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Actions Section */}
      <div className="bw-card" style={{ marginTop: 24 }}>
        <h3 style={{ margin: '0 0 16px 0' }}>Account Actions</h3>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <button className="bw-btn-outline">
            <Shield className="w-4 h-4" />
            Change Password
          </button>
          <button className="bw-btn-outline">
            <Mail className="w-4 h-4" />
            Update Email
          </button>
          <button className="bw-btn-outline">
            <Phone className="w-4 h-4" />
            Update Phone
          </button>
          <button className="bw-btn-outline">
            <MapPin className="w-4 h-4" />
            Update Address
          </button>
        </div>
      </div>
    </div>
  )
} 