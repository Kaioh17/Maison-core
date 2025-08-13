import { useEffect, useState } from 'react'
import type React from 'react'
import { getTenantInfo, getTenantDrivers, getTenantVehicles, getTenantBookings, onboardDriver, assignDriverToVehicle, type TenantResponse, type DriverResponse, type VehicleResponse, type BookingResponse, type OnboardDriver } from '@api/tenant'
import { useAuthStore } from '@store/auth'
import { useNavigate } from 'react-router-dom'
import { Car, Users, Calendar, Settings, TrendingUp, DollarSign, Clock, MapPin, User, Phone, Mail, Plus, Edit, Trash2, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

type TabType = 'overview' | 'drivers' | 'bookings' | 'vehicles' | 'settings'

export default function TenantDashboard() {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [info, setInfo] = useState<TenantResponse | null>(null)
  const [drivers, setDrivers] = useState<DriverResponse[]>([])
  const [vehicles, setVehicles] = useState<VehicleResponse[]>([])
  const [bookings, setBookings] = useState<BookingResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newDriver, setNewDriver] = useState<OnboardDriver>({ first_name: '', last_name: '', email: '', driver_type: 'outsourced' })
  const [assign, setAssign] = useState<{ vehicleId: string; driverId: string }>({ vehicleId: '', driverId: '' })
  const [showAddDriver, setShowAddDriver] = useState(false)
  const [showAssignDriver, setShowAssignDriver] = useState(false)
  const navigate = useNavigate()
  const { accessToken, role } = useAuthStore()

  // Debug authentication state
  useEffect(() => {
    console.log('Auth State:', { accessToken, role })
  }, [accessToken, role])

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      console.log('Starting to load dashboard data...')
      console.log('Auth State:', { accessToken, role, userId: useAuthStore.getState().getUserId() })
      console.log('API Base URL:', import.meta.env.VITE_API_BASE || 'http://localhost:8000/api')
      
      console.log('Making API calls...')
      const tenantInfoPromise = getTenantInfo()
      const driversPromise = getTenantDrivers()
      const vehiclesPromise = getTenantVehicles()
      const bookingsPromise = getTenantBookings()
      
      console.log('Waiting for all promises to resolve...')
      const [i, d, v, b] = await Promise.all([
        tenantInfoPromise,
        driversPromise,
        vehiclesPromise,
        bookingsPromise,
      ])
      
      console.log('=== API RESPONSES ===')
      console.log('Tenant Info Response (full):', JSON.stringify(i, null, 2))
      console.log('Tenant Drivers Response (full):', JSON.stringify(d, null, 2))
      console.log('Tenant Vehicles Response (full):', JSON.stringify(v, null, 2))
      console.log('Tenant Bookings Response (full):', JSON.stringify(b, null, 2))
      
      console.log('=== RESPONSE STRUCTURE ANALYSIS ===')
      console.log('Tenant Info - has data property?', 'data' in i)
      console.log('Tenant Info - data type:', typeof i.data)
      console.log('Tenant Info - data value:', i.data)
      
      if (i.data) {
        setInfo(i.data)
        console.log('✅ Tenant info set successfully:', i.data)
      } else {
        console.error('❌ No tenant data in response:', i)
        console.error('Response structure:', Object.keys(i))
        setError('Failed to load tenant information - no data in response')
      }
      
      // Handle drivers - empty array is valid
      if (d.data !== undefined) {
        setDrivers(d.data || [])
        console.log('✅ Drivers set successfully:', d.data || [])
      } else {
        console.error('❌ No drivers data in response:', d)
        setError('Failed to load drivers information - no data in response')
      }
      
      // Handle vehicles - empty array is valid
      if (v.data !== undefined) {
        setVehicles(v.data || [])
        console.log('✅ Vehicles set successfully:', v.data || [])
      } else {
        console.error('❌ No vehicles data in response:', v)
        setError('Failed to load vehicles information - no data in response')
      }
      
      // Handle bookings - empty array is valid
      if (b.data !== undefined) {
        setBookings(b.data || [])
        console.log('✅ Bookings set successfully:', b.data || [])
      } else {
        console.error('❌ No bookings data in response:', b)
        setError('Failed to load bookings information - no data in response')
      }
      
    } catch (error: any) {
      console.error('❌ Failed to load dashboard data:', error)
      console.error('Error name:', error.name)
      console.error('Error message:', error.message)
      console.error('Error stack:', error.stack)
      
      if (error.response) {
        console.error('Error response:', error.response.data)
        console.error('Error status:', error.response.status)
        console.error('Error headers:', error.response.headers)
        setError(`Failed to load data: ${error.response.status} - ${error.response.data?.detail || 'Unknown error'}`)
      } else if (error.request) {
        console.error('No response received:', error.request)
        console.error('Request details:', {
          method: error.request.method,
          url: error.request.url,
          headers: error.request.headers
        })
        setError('No response from server. Please check your connection and try again.')
      } else {
        console.error('Error setting up request:', error.message)
        setError('Failed to load dashboard data. Please check your connection and try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const createDriver = async () => {
    if (!newDriver.email || !newDriver.first_name || !newDriver.last_name) return
    try {
      await onboardDriver({ ...newDriver, driver_type: newDriver.driver_type as OnboardDriver['driver_type'] })
      setNewDriver({ first_name: '', last_name: '', email: '', driver_type: 'outsourced' })
      setShowAddDriver(false)
      await load()
    } catch (error) {
      console.error('Failed to create driver:', error)
    }
  }

  const assignVehicle = async () => {
    const vehicleId = Number(assign.vehicleId)
    const driverId = Number(assign.driverId)
    if (!vehicleId || !driverId) return
    try {
      await assignDriverToVehicle(vehicleId, { driver_id: driverId })
      setAssign({ vehicleId: '', driverId: '' })
      setShowAssignDriver(false)
      await load()
    } catch (error) {
      console.error('Failed to assign driver:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed': return 'text-green-500'
      case 'active': return 'text-green-500'
      case 'pending': return 'text-yellow-500'
      case 'cancelled': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'active': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'pending': return <AlertCircle className="w-4 h-4 text-yellow-500" />
      case 'cancelled': return <XCircle className="w-4 h-4 text-red-500" />
      default: return <AlertCircle className="w-4 h-4 text-gray-500" />
    }
  }

  const tabs: Array<{ id: TabType; label: string; icon: React.ComponentType<{ className?: string }> }> = [
    { id: 'overview', label: 'Overview', icon: TrendingUp },
    { id: 'drivers', label: 'Drivers', icon: Users },
    { id: 'bookings', label: 'Bookings', icon: Calendar },
    { id: 'vehicles', label: 'Vehicles', icon: Car },
    { id: 'settings', label: 'Settings', icon: Settings },
  ]

  if (loading) {
    return (
      <div className="bw bw-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div className="bw-loading">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bw bw-container" style={{ padding: '24px 0' }}>
        <div className="bw-header" style={{ marginBottom: 32 }}>
          <div className="bw-header-content">
            <h1 style={{ fontSize: 32, margin: 0 }}>Dashboard</h1>
            <div className="bw-header-actions">
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
        
        <div className="bw-card" style={{ textAlign: 'center', padding: '48px 24px' }}>
          <div style={{ color: '#ef4444', marginBottom: '16px' }}>
            <AlertCircle className="w-12 h-12 mx-auto" />
          </div>
          <h3 style={{ margin: '0 0 16px 0', color: '#ef4444' }}>Error Loading Dashboard</h3>
          <p style={{ margin: '0 0 24px 0', color: '#6b7280' }}>{error}</p>
          <button 
            className="bw-btn" 
            onClick={load}
            style={{ color: '#000' }}
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (!info) {
    return (
      <div className="bw bw-container" style={{ padding: '24px 0' }}>
        <div className="bw-header" style={{ marginBottom: 32 }}>
          <div className="bw-header-content">
            <h1 style={{ fontSize: 32, margin: 0 }}>Dashboard</h1>
            <div className="bw-header-actions">
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
        
        <div className="bw-card" style={{ textAlign: 'center', padding: '48px 24px' }}>
          <div style={{ color: '#6b7280', marginBottom: '16px' }}>
            <AlertCircle className="w-12 h-12 mx-auto" />
          </div>
          <h3 style={{ margin: '0 0 16px 0', color: '#6b7280' }}>No Tenant Information</h3>
          <p style={{ margin: '0 0 24px 0', color: '#6b7280' }}>Unable to load tenant information. Please try again.</p>
          <button 
            className="bw-btn" 
            onClick={load}
            style={{ color: '#000' }}
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bw bw-container" style={{ padding: '24px 0' }}>
      {/* Header */}
      <div className="bw-header" style={{ marginBottom: 32 }}>
        <div className="bw-header-content">
          <h1 style={{ fontSize: 32, margin: 0 }}>Dashboard</h1>
          <div className="bw-header-actions">
            <span className="bw-text-muted">Welcome back, {info?.first_name}</span>
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

      {/* Tabs */}
      <div className="bw-tabs" style={{ marginBottom: 32 }}>
        {tabs.map((tab) => {
          const IconComponent = tab.icon
          return (
            <button
              key={tab.id}
              className={`bw-tab ${activeTab === tab.id ? 'bw-tab-active' : ''}`}
              onClick={() => setActiveTab(tab.id as TabType)}
            >
              <IconComponent className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      <div className="bw-tab-content">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="bw-grid" style={{ gap: 24 }}>
            {/* Stats Cards */}
            <div className="bw-card" style={{ gridColumn: 'span 3' }}>
              <div className="bw-stat">
                <div className="bw-stat-icon" style={{ background: 'var(--bw-accent)' }}>
                  <Users className="w-6 h-6" />
                </div>
                <div className="bw-stat-content">
                  <div className="bw-stat-value">{drivers.length}</div>
                  <div className="bw-stat-label">Total Drivers</div>
                </div>
              </div>
            </div>

            <div className="bw-card" style={{ gridColumn: 'span 3' }}>
              <div className="bw-stat">
                <div className="bw-stat-icon" style={{ background: 'var(--bw-accent)' }}>
                  <Car className="w-6 h-6" />
                </div>
                <div className="bw-stat-content">
                  <div className="bw-stat-value">{vehicles.length}</div>
                  <div className="bw-stat-label">Total Vehicles</div>
                </div>
              </div>
            </div>

            <div className="bw-card" style={{ gridColumn: 'span 3' }}>
              <div className="bw-stat">
                <div className="bw-stat-icon" style={{ background: 'var(--bw-accent)' }}>
                  <Calendar className="w-6 h-6" />
                </div>
                <div className="bw-stat-content">
                  <div className="bw-stat-value">{bookings.length}</div>
                  <div className="bw-stat-label">Total Bookings</div>
                </div>
              </div>
            </div>

            <div className="bw-card" style={{ gridColumn: 'span 3' }}>
              <div className="bw-stat">
                <div className="bw-stat-icon" style={{ background: 'var(--bw-accent)' }}>
                  <DollarSign className="w-6 h-6" />
                </div>
                <div className="bw-stat-content">
                  <div className="bw-stat-value">{info?.subscription_plan || 'N/A'}</div>
                  <div className="bw-stat-label">Subscription Plan</div>
                </div>
              </div>
            </div>

            {/* Company Info */}
            <div className="bw-card" style={{ gridColumn: 'span 6' }}>
              <h3 style={{ margin: '0 0 16px 0' }}>Company Information</h3>
              <div className="bw-info-grid">
                <div className="bw-info-item">
                  <span className="bw-info-label">Company Name:</span>
                  <span className="bw-info-value">{info?.company_name}</span>
                </div>
                <div className="bw-info-item">
                  <span className="bw-info-label">City:</span>
                  <span className="bw-info-value">{info?.city}</span>
                </div>
                <div className="bw-info-item">
                  <span className="bw-info-label">Status:</span>
                  <span className={`bw-info-value ${info?.is_verified ? 'text-green-500' : 'text-yellow-500'}`}>
                    {info?.is_verified ? 'Verified' : 'Pending Verification'}
                  </span>
                </div>
                <div className="bw-info-item">
                  <span className="bw-info-label">Member Since:</span>
                  <span className="bw-info-value">
                    {new Date(info?.created_on).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bw-card" style={{ gridColumn: 'span 6' }}>
              <h3 style={{ margin: '0 0 16px 0' }}>Recent Bookings</h3>
              <div className="bw-recent-list">
                {bookings.slice(0, 5).map((booking) => (
                  <div key={booking.id} className="bw-recent-item">
                    <div className="bw-recent-icon">
                      <MapPin className="w-4 h-4" />
                    </div>
                    <div className="bw-recent-content">
                      <div className="bw-recent-title">
                        {booking.pickup_location} → {booking.dropoff_location}
                      </div>
                      <div className="bw-recent-meta">
                        {new Date(booking.pickup_time).toLocaleDateString()} • {booking.service_type}
                      </div>
                    </div>
                    <div className="bw-recent-status">
                      {getStatusIcon(booking.booking_status)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Drivers Tab */}
        {activeTab === 'drivers' && (
          <div className="bw-content">
            <div className="bw-content-header">
              <h3>Driver Management</h3>
              <button 
                className="bw-btn" 
                onClick={() => setShowAddDriver(true)}
                style={{ color: '#000' }}
              >
                <Plus className="w-4 h-4" />
                Add Driver
              </button>
            </div>

            <div className="bw-card">
              <div className="bw-table">
                <div className="bw-table-header">
                  <div className="bw-table-cell">Driver</div>
                  <div className="bw-table-cell">Contact</div>
                  <div className="bw-table-cell">Type</div>
                  <div className="bw-table-cell">Status</div>
                  <div className="bw-table-cell">Rides</div>
                  <div className="bw-table-cell">Actions</div>
                </div>
                {drivers.length === 0 ? (
                  <div className="bw-empty-state">
                    <div className="bw-empty-icon">
                      <User className="w-8 h-8" />
                    </div>
                    <div className="bw-empty-text">No drivers yet</div>
                    <div className="bw-empty-subtext">Add your first driver to get started</div>
                  </div>
                ) : (
                  drivers.map((driver) => (
                    <div key={driver.id} className="bw-table-row">
                      <div className="bw-table-cell">
                        <div className="bw-user-info">
                          <div className="bw-user-avatar">
                            <User className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="bw-user-name">{driver.first_name} {driver.last_name}</div>
                            <div className="bw-user-email">{driver.email}</div>
                          </div>
                        </div>
                      </div>
                      <div className="bw-table-cell">
                        <div className="bw-contact-info">
                          <div className="bw-contact-item">
                            <Phone className="w-3 h-3" />
                            {driver.phone_no}
                          </div>
                        </div>
                      </div>
                      <div className="bw-table-cell">
                        <span className={`bw-badge ${driver.driver_type === 'in_house' ? 'bw-badge-primary' : 'bw-badge-secondary'}`}>
                          {driver.driver_type === 'in_house' ? 'In-House' : 'Outsourced'}
                        </span>
                      </div>
                      <div className="bw-table-cell">
                        <span className={`bw-badge ${driver.is_active ? 'bw-badge-success' : 'bw-badge-warning'}`}>
                          {driver.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <div className="bw-table-cell">
                        {driver.completed_rides}
                      </div>
                      <div className="bw-table-cell">
                        <div className="bw-actions">
                          <button className="bw-btn-icon">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button className="bw-btn-icon bw-btn-icon-danger">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Bookings Tab */}
        {activeTab === 'bookings' && (
          <div className="bw-content">
            <div className="bw-content-header">
              <h3>Booking Management</h3>
            </div>

            <div className="bw-card">
              <div className="bw-table">
                <div className="bw-table-header">
                  <div className="bw-table-cell">ID</div>
                  <div className="bw-table-cell">Route</div>
                  <div className="bw-table-cell">Service</div>
                  <div className="bw-table-cell">Date & Time</div>
                  <div className="bw-table-cell">Status</div>
                  <div className="bw-table-cell">Price</div>
                </div>
                {bookings.length === 0 ? (
                  <div className="bw-empty-state">
                    <div className="bw-empty-icon">
                      <Calendar className="w-8 h-8" />
                    </div>
                    <div className="bw-empty-text">No bookings yet</div>
                    <div className="bw-empty-subtext">Bookings will appear here once riders start using your service</div>
                  </div>
                ) : (
                  bookings.map((booking) => (
                    <div key={booking.id} className="bw-table-row">
                      <div className="bw-table-cell">#{booking.id}</div>
                      <div className="bw-table-cell">
                        <div className="bw-route-info">
                          <div className="bw-route-item">
                            <MapPin className="w-3 h-3" />
                            {booking.pickup_location}
                          </div>
                          {booking.dropoff_location && (
                            <div className="bw-route-item">
                              <MapPin className="w-3 h-3" />
                              {booking.dropoff_location}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="bw-table-cell">
                        <span className="bw-badge bw-badge-secondary">
                          {booking.service_type}
                        </span>
                      </div>
                      <div className="bw-table-cell">
                        <div className="bw-datetime-info">
                          <div>{new Date(booking.pickup_time).toLocaleDateString()}</div>
                          <div className="bw-text-muted">
                            {new Date(booking.pickup_time).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                      <div className="bw-table-cell">
                        {getStatusIcon(booking.booking_status)}
                        <span className={getStatusColor(booking.booking_status)}>
                          {booking.booking_status}
                        </span>
                      </div>
                      <div className="bw-table-cell">
                        {booking.estimated_price ? `$${booking.estimated_price}` : 'N/A'}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Vehicles Tab */}
        {activeTab === 'vehicles' && (
          <div className="bw-content">
            <div className="bw-content-header">
              <h3>Vehicle Management</h3>
              <button 
                className="bw-btn" 
                onClick={() => setShowAssignDriver(true)}
                style={{ color: '#000' }}
              >
                <Plus className="w-4 h-4" />
                Assign Driver
              </button>
            </div>

            <div className="bw-card">
              <div className="bw-table">
                <div className="bw-table-header">
                  <div className="bw-table-cell">Vehicle</div>
                  <div className="bw-table-cell">Category</div>
                  <div className="bw-table-cell">Capacity</div>
                  <div className="bw-table-cell">Rate</div>
                  <div className="bw-table-cell">Status</div>
                  <div className="bw-table-cell">Actions</div>
                </div>
                {vehicles.length === 0 ? (
                  <div className="bw-empty-state">
                    <div className="bw-empty-icon">
                      <Car className="w-8 h-8" />
                    </div>
                    <div className="bw-empty-text">No vehicles yet</div>
                    <div className="bw-empty-subtext">Add vehicles to your fleet to start accepting rides</div>
                  </div>
                ) : (
                  vehicles.map((vehicle) => (
                    <div key={vehicle.id} className="bw-table-row">
                      <div className="bw-table-cell">
                        <div className="bw-vehicle-info">
                          <div className="bw-vehicle-icon">
                            <Car className="w-5 h-5" />
                          </div>
                          <div>
                            <div className="bw-vehicle-name">
                              {vehicle.year} {vehicle.make} {vehicle.model}
                            </div>
                            <div className="bw-vehicle-details">
                              {vehicle.color} • {vehicle.license_plate}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="bw-table-cell">
                        <span className="bw-badge bw-badge-secondary">
                          {vehicle.vehicle_config?.vehicle_category}
                        </span>
                      </div>
                      <div className="bw-table-cell">
                        {vehicle.vehicle_config?.seating_capacity} seats
                      </div>
                      <div className="bw-table-cell">
                        ${vehicle.vehicle_config?.vehicle_flat_rate}
                      </div>
                      <div className="bw-table-cell">
                        <span className={`bw-badge ${vehicle.status === 'active' ? 'bw-badge-success' : 'bw-badge-warning'}`}>
                          {vehicle.status || 'Unknown'}
                        </span>
                      </div>
                      <div className="bw-table-cell">
                        <div className="bw-actions">
                          <button className="bw-btn-icon">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button className="bw-btn-icon bw-btn-icon-danger">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="bw-content">
            <div className="bw-content-header">
              <h3>Tenant Settings</h3>
              <button 
                className="bw-btn-outline" 
                onClick={() => navigate('/tenant_settings')}
              >
                <Settings className="w-4 h-4" />
                Manage Settings
              </button>
            </div>

            <div className="bw-card">
              <h4 style={{ margin: '0 0 16px 0' }}>Account Information</h4>
              <div className="bw-info-grid">
                <div className="bw-info-item">
                  <span className="bw-info-label">Email:</span>
                  <span className="bw-info-value">{info?.email}</span>
                </div>
                <div className="bw-info-item">
                  <span className="bw-info-label">Phone:</span>
                  <span className="bw-info-value">{info?.phone_no}</span>
                </div>
                <div className="bw-info-item">
                  <span className="bw-info-label">Address:</span>
                  <span className="bw-info-value">{info?.address || 'Not provided'}</span>
                </div>
                <div className="bw-info-item">
                  <span className="bw-info-label">Stripe Customer ID:</span>
                  <span className="bw-info-value">{info?.stripe_customer_id || 'Not connected'}</span>
                </div>
              </div>
            </div>

            <div className="bw-card">
              <h4 style={{ margin: '0 0 16px 0' }}>System Tools</h4>
              <div className="bw-info-grid">
                <div className="bw-info-item">
                  <span className="bw-info-label">Frontend Logs:</span>
                  <div className="bw-info-value">
                    <button 
                      className="bw-btn-outline" 
                      onClick={() => {
                        if (window.maisonLogs) {
                          window.maisonLogs.downloadLogs()
                        } else {
                          console.error('Logging system not available')
                        }
                      }}
                      style={{ fontSize: '14px', padding: '4px 8px' }}
                    >
                      Download Logs
                    </button>
                    <span style={{ marginLeft: '8px', fontSize: '12px', color: '#6b7280' }}>
                      {window.maisonLogs ? `${window.maisonLogs.getLogCount()} entries` : 'Not available'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Driver Modal */}
      {showAddDriver && (
        <div className="bw-modal-overlay" onClick={() => setShowAddDriver(false)}>
          <div className="bw-modal" onClick={(e: React.MouseEvent<HTMLDivElement>) => e.stopPropagation()}>
            <div className="bw-modal-header">
              <h3>Add New Driver</h3>
              <button className="bw-btn-icon" onClick={() => setShowAddDriver(false)}>
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <div className="bw-modal-body">
              <div className="bw-form-grid">
                <div className="bw-form-group">
                  <label>First Name</label>
                  <input 
                    className="bw-input" 
                    value={newDriver.first_name} 
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewDriver({ ...newDriver, first_name: e.target.value })} 
                  />
                </div>
                <div className="bw-form-group">
                  <label>Last Name</label>
                  <input 
                    className="bw-input" 
                    value={newDriver.last_name} 
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewDriver({ ...newDriver, last_name: e.target.value })} 
                  />
                </div>
                <div className="bw-form-group">
                  <label>Email</label>
                  <input 
                    className="bw-input" 
                    type="email" 
                    value={newDriver.email} 
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewDriver({ ...newDriver, email: e.target.value })} 
                  />
                </div>
                <div className="bw-form-group">
                  <label>Driver Type</label>
                  <select 
                    className="bw-input" 
                    value={newDriver.driver_type} 
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setNewDriver({ ...newDriver, driver_type: e.target.value as OnboardDriver['driver_type'] })}
                  >
                    <option value="outsourced">Outsourced</option>
                    <option value="in_house">In-House</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="bw-modal-footer">
              <button className="bw-btn-outline" onClick={() => setShowAddDriver(false)}>
                Cancel
              </button>
              <button 
                className="bw-btn" 
                onClick={createDriver}
                style={{ color: '#000' }}
              >
                Create Driver
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Assign Driver Modal */}
      {showAssignDriver && (
        <div className="bw-modal-overlay" onClick={() => setShowAssignDriver(false)}>
          <div className="bw-modal" onClick={(e: React.MouseEvent<HTMLDivElement>) => e.stopPropagation()}>
            <div className="bw-modal-header">
              <h3>Assign Driver to Vehicle</h3>
              <button className="bw-btn-icon" onClick={() => setShowAssignDriver(false)}>
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <div className="bw-modal-body">
              <div className="bw-form-grid">
                <div className="bw-form-group">
                  <label>Vehicle</label>
                  <select 
                    className="bw-input" 
                    value={assign.vehicleId} 
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setAssign({ ...assign, vehicleId: e.target.value })}
                  >
                    <option value="">Select vehicle</option>
                    {vehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.year} {v.make} {v.model}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="bw-form-group">
                  <label>Driver</label>
                  <select 
                    className="bw-input" 
                    value={assign.driverId} 
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setAssign({ ...assign, driverId: e.target.value })}
                  >
                    <option value="">Select driver</option>
                    {drivers.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.first_name} {d.last_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            <div className="bw-modal-footer">
              <button className="bw-btn-outline" onClick={() => setShowAssignDriver(false)}>
                Cancel
              </button>
              <button 
                className="bw-btn" 
                onClick={assignVehicle}
                style={{ color: '#000' }}
              >
                Assign Driver
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 