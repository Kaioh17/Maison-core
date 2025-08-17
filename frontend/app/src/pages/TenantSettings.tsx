import { useState, useEffect } from 'react'
import { getTenantInfo } from '@api/tenant'
import { getTenantSettings, updateTenantSettings, type TenantSettingsResponse, type UpdateTenantSetting } from '@api/tenantSettings'
import { useAuthStore } from '@store/auth'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Settings, User, Building, MapPin, Phone, Mail, Shield, CreditCard, DollarSign, Clock, Car, Palette, Save, Edit } from 'lucide-react'

export default function TenantSettings() {
  const [info, setInfo] = useState<any>(null)
  const [tenantSettings, setTenantSettings] = useState<TenantSettingsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [editingSettings, setEditingSettings] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editedSettings, setEditedSettings] = useState<UpdateTenantSetting | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const loadData = async () => {
      try {
        const [tenantInfo, settings] = await Promise.all([
          getTenantInfo(),
          getTenantSettings()
        ])
        setInfo(tenantInfo.data)
        setTenantSettings(settings)
        setEditedSettings(settings)
      } catch (error) {
        console.error('Failed to load data:', error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const handleSettingChange = (field: keyof UpdateTenantSetting, value: any) => {
    if (editedSettings) {
      setEditedSettings({
        ...editedSettings,
        [field]: value
      })
    }
  }

  const handleSaveSettings = async () => {
    if (!editedSettings) return
    
    try {
      setSaving(true)
      const updatedSettings = await updateTenantSettings(editedSettings)
      setTenantSettings(updatedSettings)
      setEditingSettings(false)
      alert('Settings updated successfully!')
    } catch (error) {
      console.error('Failed to update settings:', error)
      alert('Failed to update settings. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleCancelEdit = () => {
    setEditedSettings(tenantSettings)
    setEditingSettings(false)
  }

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

      {/* Tenant Settings Section */}
      {tenantSettings && (
        <div className="bw-card" style={{ marginTop: 24 }}>
          <div className="bw-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0 }}>Tenant Settings</h3>
            <div style={{ display: 'flex', gap: 8 }}>
              {editingSettings ? (
                <>
                  <button 
                    className="bw-btn-outline" 
                    onClick={handleCancelEdit}
                    disabled={saving}
                  >
                    Cancel
                  </button>
                  <button 
                    className="bw-btn" 
                    onClick={handleSaveSettings}
                    disabled={saving}
                  >
                    {saving ? 'Saving...' : (
                      <>
                        <Save className="w-4 h-4" />
                        Save Changes
                      </>
                    )}
                  </button>
                </>
              ) : (
                <button 
                  className="bw-btn-outline" 
                  onClick={() => setEditingSettings(true)}
                >
                  <Edit className="w-4 h-4" />
                  Edit Settings
                </button>
              )}
            </div>
          </div>

          {/* Branding & Theme Settings */}
          <div style={{ marginBottom: 32 }}>
            <h4 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Palette className="w-4 h-4" />
              Branding & Theme
            </h4>
            <div className="bw-form-grid" style={{ display: 'grid', gap: '16px', gridTemplateColumns: '1fr 1fr' }}>
              <div className="bw-form-group">
                <label className="bw-form-label">Theme</label>
                {editingSettings ? (
                  <select 
                    className="bw-input" 
                    value={editedSettings?.theme || ''} 
                    onChange={(e) => handleSettingChange('theme', e.target.value)}
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                    <option value="auto">Auto</option>
                  </select>
                ) : (
                  <span className="bw-info-value">{tenantSettings.theme || 'Not set'}</span>
                )}
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Logo URL</label>
                {editingSettings ? (
                  <input 
                    className="bw-input" 
                    type="text" 
                    value={editedSettings?.logo_url || ''} 
                    onChange={(e) => handleSettingChange('logo_url', e.target.value)}
                    placeholder="https://example.com/logo.png"
                  />
                ) : (
                  <span className="bw-info-value">{tenantSettings.logo_url || 'Not set'}</span>
                )}
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Slug</label>
                {editingSettings ? (
                  <input 
                    className="bw-input" 
                    type="text" 
                    value={editedSettings?.slug || ''} 
                    onChange={(e) => handleSettingChange('slug', e.target.value)}
                    placeholder="company-name"
                  />
                ) : (
                  <span className="bw-info-value">{tenantSettings.slug || 'Not set'}</span>
                )}
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Enable Branding</label>
                {editingSettings ? (
                  <select 
                    className="bw-input" 
                    value={editedSettings?.enable_branding ? 'true' : 'false'} 
                    onChange={(e) => handleSettingChange('enable_branding', e.target.value === 'true')}
                  >
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                ) : (
                  <span className="bw-info-value">{tenantSettings.enable_branding ? 'Yes' : 'No'}</span>
                )}
              </div>
            </div>
          </div>

          {/* Fare Settings */}
          <div style={{ marginBottom: 32 }}>
            <h4 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
              <DollarSign className="w-4 h-4" />
              Fare Configuration
            </h4>
            <div className="bw-form-grid" style={{ display: 'grid', gap: '16px', gridTemplateColumns: '1fr 1fr' }}>
              <div className="bw-form-group">
                <label className="bw-form-label">Base Fare ($)</label>
                {editingSettings ? (
                  <input 
                    className="bw-input" 
                    type="number" 
                    step="0.01" 
                    min="0"
                    value={editedSettings?.base_fare || 0} 
                    onChange={(e) => handleSettingChange('base_fare', parseFloat(e.target.value) || 0)}
                    placeholder="5.00"
                  />
                ) : (
                  <span className="bw-info-value">${tenantSettings.base_fare || 0}</span>
                )}
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Per Minute Rate ($)</label>
                {editingSettings ? (
                  <input 
                    className="bw-input" 
                    type="number" 
                    step="0.01" 
                    min="0"
                    value={editedSettings?.per_minute_rate || 0} 
                    onChange={(e) => handleSettingChange('per_minute_rate', parseFloat(e.target.value) || 0)}
                    placeholder="0.50"
                  />
                ) : (
                  <span className="bw-info-value">${tenantSettings.per_minute_rate || 0}</span>
                )}
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Per Mile Rate ($)</label>
                {editingSettings ? (
                  <input 
                    className="bw-input" 
                    type="number" 
                    step="0.01" 
                    min="0"
                    value={editedSettings?.per_mile_rate || 0} 
                    onChange={(e) => handleSettingChange('per_mile_rate', parseFloat(e.target.value) || 0)}
                    placeholder="2.50"
                  />
                ) : (
                  <span className="bw-info-value">${tenantSettings.per_mile_rate || 0}</span>
                )}
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Per Hour Rate ($)</label>
                {editingSettings ? (
                  <input 
                    className="bw-input" 
                    type="number" 
                    step="0.01" 
                    min="0"
                    value={editedSettings?.per_hour_rate || 0} 
                    onChange={(e) => handleSettingChange('per_hour_rate', parseFloat(e.target.value) || 0)}
                    placeholder="25.00"
                  />
                ) : (
                  <span className="bw-info-value">${tenantSettings.per_hour_rate || 0}</span>
                )}
              </div>
            </div>
          </div>

          {/* Rider Settings */}
          <div style={{ marginBottom: 32 }}>
            <h4 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
              <User className="w-4 h-4" />
              Rider Configuration
            </h4>
            <div className="bw-form-grid" style={{ display: 'grid', gap: '16px', gridTemplateColumns: '1fr 1fr' }}>
              <div className="bw-form-group">
                <label className="bw-form-label">Rider Tiers Enabled</label>
                {editingSettings ? (
                  <select 
                    className="bw-input" 
                    value={editedSettings?.rider_tiers_enabled ? 'true' : 'false'} 
                    onChange={(e) => handleSettingChange('rider_tiers_enabled', e.target.value === 'true')}
                  >
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                ) : (
                  <span className="bw-info-value">{tenantSettings.rider_tiers_enabled ? 'Yes' : 'No'}</span>
                )}
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Cancellation Fee ($)</label>
                {editingSettings ? (
                  <input 
                    className="bw-input" 
                    type="number" 
                    step="0.01" 
                    min="0"
                    value={editedSettings?.cancellation_fee || 0} 
                    onChange={(e) => handleSettingChange('cancellation_fee', parseFloat(e.target.value) || 0)}
                    placeholder="10.00"
                  />
                ) : (
                  <span className="bw-info-value">${tenantSettings.cancellation_fee || 0}</span>
                )}
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Discounts Enabled</label>
                {editingSettings ? (
                  <select 
                    className="bw-input" 
                    value={editedSettings?.discounts ? 'true' : 'false'} 
                    onChange={(e) => handleSettingChange('discounts', e.target.value === 'true')}
                  >
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                ) : (
                  <span className="bw-info-value">{tenantSettings.discounts ? 'Yes' : 'No'}</span>
                )}
              </div>
            </div>
          </div>

          {/* Last Updated Info */}
          <div style={{ 
            padding: '16px', 
            backgroundColor: '#f8fafc', 
            borderRadius: '4px', 
            border: '1px solid #e2e8f0',
            marginTop: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#6b7280', fontSize: '14px' }}>
              <Clock className="w-4 h-4" />
              Last updated: {tenantSettings.updated_on ? new Date(tenantSettings.updated_on).toLocaleString() : 'Never'}
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 