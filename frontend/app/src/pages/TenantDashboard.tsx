import { useEffect, useState } from 'react'
import type React from 'react'
import { getTenantInfo, getTenantDrivers, getTenantVehicles, getTenantBookings, onboardDriver, assignDriverToVehicle, type TenantResponse, type DriverResponse, type VehicleResponse, type BookingResponse, type OnboardDriver } from '@api/tenant'
import { getVehicleRates, getVehicleCategories, createVehicleCategory, setVehicleRates } from '@api/vehicles'
import { useAuthStore } from '@store/auth'
import { useNavigate } from 'react-router-dom'
import { Car, Users, Calendar, Settings, TrendingUp, DollarSign, Clock, MapPin, User, Phone, Mail, Plus, Edit, Trash2, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { API_BASE } from '@config'

type TabType = 'overview' | 'drivers' | 'bookings' | 'vehicles' | 'settings'

export default function TenantDashboard() {
  const { accessToken, role } = useAuthStore()
  const navigate = useNavigate()
  const [info, setInfo] = useState<any>(null)
  const [drivers, setDrivers] = useState<DriverResponse[]>([])
  const [vehicles, setVehicles] = useState<VehicleResponse[]>([])
  const [bookings, setBookings] = useState<BookingResponse[]>([])
  const [vehicleCategories, setVehicleCategories] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [addingCategory, setAddingCategory] = useState(false)
  const [editingRates, setEditingRates] = useState<{ [key: string]: number }>({})
  const [savingRates, setSavingRates] = useState<{ [key: string]: boolean }>({})
  const [newDriver, setNewDriver] = useState<OnboardDriver>({ first_name: '', last_name: '', email: '', driver_type: 'outsourced' })
  const [assign, setAssign] = useState<{ vehicleId: string; driverId: string }>({ vehicleId: '', driverId: '' })
  const [showAddDriver, setShowAddDriver] = useState(false)
  const [showAssignDriver, setShowAssignDriver] = useState(false)
  const [activeTab, setActiveTab] = useState<TabType>('overview')

  // Debug authentication state
  useEffect(() => {
    console.log('Auth State:', { accessToken, role })
  }, [accessToken, role])

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      console.log('Starting to load dashboard data...')
      
      const tenantInfoPromise = getTenantInfo()
      const driversPromise = getTenantDrivers()
      const vehiclesPromise = getTenantVehicles()
      const bookingsPromise = getTenantBookings()
      const vehicleCategoriesPromise = getVehicleCategories()
      
      const [i, d, v, b, vc] = await Promise.all([
        tenantInfoPromise,
        driversPromise,
        vehiclesPromise,
        bookingsPromise,
        vehicleCategoriesPromise,
      ])
      
      if (i.data) {
        setInfo(i.data)
      } else {
        console.error('No tenant data in response:', i)
        setError('Failed to load tenant information - no data in response')
      }
      
      // Handle drivers - empty array is valid
      if (d.data !== undefined) {
        setDrivers(d.data || [])
      } else {
        console.error('No drivers data in response:', d)
        setError('Failed to load drivers information - no data in response')
      }
      
      // Handle vehicles - empty array is valid
      if (v.data !== undefined) {
        setVehicles(v.data || [])
      } else {
        console.error('No vehicles data in response:', v)
        setError('Failed to load vehicles information - no data in response')
      }
      
      // Handle bookings - empty array is valid
      if (b.data !== undefined) {
        setBookings(b.data || [])
      } else {
        console.error('No bookings data in response:', b)
        setError('Failed to load bookings information - no data in response')
      }
      
      // Handle vehicle categories
      if (vc.data !== undefined) {
        setVehicleCategories(vc.data || [])
      } else if (vc && Array.isArray(vc)) {
        // Handle case where response is directly an array
        setVehicleCategories(vc)
      } else {
        setVehicleCategories([])
      }
      
    } catch (error: any) {
      console.error('Failed to load dashboard data:', error)
      
      if (error.response) {
        setError(`Failed to load data: ${error.response.status} - ${error.response.data?.detail || 'Unknown error'}`)
      } else if (error.request) {
        setError('No response from server. Please check your connection and try again.')
      } else {
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

  const saveVehicleRate = async (categoryName: string, newRate: number) => {
    try {
      setSavingRates(prev => {
        try {
          return { ...prev, [categoryName]: true }
        } catch (e) {
          console.error('Error updating saving state:', e)
          return prev
        }
      })
      
      const payload = {
        vehicle_category: categoryName,
        vehicle_flat_rate: newRate
      }
      
      const result = await setVehicleRates(payload)
      
      // Update local state to reflect the change
      setVehicleCategories(prev => {
        try {
          return prev.map(cat => 
            cat.vehicle_category === categoryName 
              ? { ...cat, vehicle_flat_rate: newRate }
              : cat
          )
        } catch (e) {
          console.error('Error updating vehicle categories state:', e)
          return prev
        }
      })
      
      // Clear the editing state for this category
      setEditingRates(prev => {
        try {
          const newState = { ...prev }
          delete newState[categoryName]
          return newState
        } catch (e) {
          console.error('Error clearing editing state:', e)
          return prev
        }
      })
      
      alert(`Successfully updated ${categoryName} rate to $${newRate}`)
    } catch (error: any) {
      console.error(`Failed to update ${categoryName} rate:`, error)
      alert(`Failed to update ${categoryName} rate. Please try again.`)
    } finally {
      // Safely reset saving state
      setSavingRates(prev => {
        try {
          return { ...prev, [categoryName]: false }
        } catch (e) {
          console.error('Error resetting saving state:', e)
          return prev
        }
      })
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

  const getVehicleRate = (category: string) => {
    // Check if vehicleCategories is an array and has items
    if (!vehicleCategories || !Array.isArray(vehicleCategories) || vehicleCategories.length === 0) {
      // Return default rates if no API data available
      const defaultRates: { [key: string]: number } = {
        'sedan': 25.00,
        'suv': 35.00,
        'luxury': 50.00,
        'van': 40.00,
        'truck': 45.00,
        'motorcycle': 20.00
      }
      return defaultRates[category] || 0
    }
    
    // Look for the category in vehicleCategories
    const categoryData = vehicleCategories.find(cat => cat.vehicle_category === category)
    if (categoryData && categoryData.vehicle_flat_rate > 0) {
      return categoryData.vehicle_flat_rate
    }
    
    // Return default rates if no API data available
    const defaultRates: { [key: string]: number } = {
      'sedan': 25.00,
      'suv': 35.00,
      'luxury': 50.00,
      'van': 40.00,
      'truck': 45.00,
      'motorcycle': 20.00
    }
    return defaultRates[category] || 0
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

  // Error boundary for the component
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
            onClick={() => {
              setError(null)
              load()
            }}
            style={{ color: '#000' }}
          >
            Try Again
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
              <button 
                className="bw-btn" 
                onClick={() => navigate('/vehicles/add')}
                style={{ color: '#000', marginLeft: 16 }}
              >
                <Plus className="w-4 h-4" />
                Add Vehicle
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
                  vehicles.map((vehicle) => {
                    // Debug logging to see vehicle structure
                    console.log('Vehicle data:', vehicle)
                    console.log('Vehicle config:', vehicle.vehicle_config)
                    console.log('Vehicle rate:', vehicle.vehicle_config?.vehicle_flat_rate)
                    
                    return (
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
                          {(() => {
                            const rate = getVehicleRate(vehicle.vehicle_config?.vehicle_category)
                            if (rate > 0) {
                              return `$${rate.toFixed(2)}`
                            } else if (vehicle.vehicle_config?.vehicle_flat_rate && vehicle.vehicle_config.vehicle_flat_rate > 0) {
                              return `$${vehicle.vehicle_config.vehicle_flat_rate.toFixed(2)}`
                            } else {
                              return <span style={{ color: '#6b7280', fontStyle: 'italic' }}>Not set</span>
                            }
                          })()}
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
                    )
                  })
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

            <div className="bw-card">
              <h4 style={{ margin: '0 0 16px 0' }}>Vehicle Settings</h4>
              <div style={{ marginBottom: 16 }}>
                <p className="small-muted" style={{ margin: 0 }}>
                  Configure default rates and settings for different vehicle categories
                </p>
              </div>
              
              {/* Add New Category Section */}
              <div style={{ 
                marginBottom: 24, 
                padding: '16px', 
                backgroundColor: '#f8fafc', 
                border: '1px solid #e2e8f0', 
                borderRadius: '4px' 
              }}>
                <h5 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#374151' }}>Add New Category</h5>
                <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: '1fr 1fr 1fr auto' }}>
                  <input
                    type="text"
                    placeholder="Category name (e.g., electric)"
                    className="bw-input"
                    style={{ fontSize: '14px' }}
                    id="newCategoryName"
                  />
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="Base rate ($)"
                    className="bw-input"
                    style={{ fontSize: '14px' }}
                    id="newCategoryRate"
                  />
                  <input
                    type="number"
                    min="1"
                    max="20"
                    placeholder="Seating capacity"
                    className="bw-input"
                    style={{ fontSize: '14px' }}
                    id="newCategoryCapacity"
                  />
                  <button
                    className="bw-btn"
                    style={{ fontSize: '14px', padding: '8px 16px' }}
                    disabled={addingCategory}
                    onClick={async () => {
                      const nameInput = document.getElementById('newCategoryName') as HTMLInputElement
                      const rateInput = document.getElementById('newCategoryRate') as HTMLInputElement
                      const capacityInput = document.getElementById('newCategoryCapacity') as HTMLInputElement
                      
                      const name = nameInput.value.trim()
                      const rate = parseFloat(rateInput.value) || 0
                      const capacity = parseInt(capacityInput.value) || 1
                      
                      if (name && rate > 0 && capacity > 0) {
                        setAddingCategory(true)
                        try {
                          await createVehicleCategory({ 
                            vehicle_category: name, 
                            vehicle_flat_rate: rate, 
                            seating_capacity: capacity 
                          })
                          
                          // Clear inputs after successful creation
                          nameInput.value = ''
                          rateInput.value = ''
                          capacityInput.value = ''
                          
                          alert('New category added successfully!')
                          await load() // Refresh data
                        } catch (error) {
                          console.error('Failed to add new category:', error)
                          alert('Failed to add new category. Please try again.')
                        } finally {
                          setAddingCategory(false)
                        }
                      } else {
                        alert('Please fill all fields with valid values')
                      }
                    }}
                  >
                    {addingCategory ? (
                      <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <Plus className="w-4 h-4" />
                    )}
                    Add
                  </button>
                </div>
              </div>
              
              <div className="bw-table">
                <div className="bw-table-header">
                  <div className="bw-table-cell">Vehicle Category</div>
                  <div className="bw-table-cell">Base Rate ($)</div>
                  <div className="bw-table-cell">Actions</div>
                </div>
                
                {/* Dynamic vehicle categories from API */}
                {vehicleCategories.length > 0 ? (
                  vehicleCategories.map((category) => {
                    const defaultRate = getVehicleRate(category.vehicle_category)
                    const currentRate = editingRates[category.vehicle_category] !== undefined 
                      ? editingRates[category.vehicle_category] 
                      : (category.vehicle_flat_rate > 0 ? category.vehicle_flat_rate : defaultRate)
                    const isSaving = savingRates[category.vehicle_category] || false
                    
                    return (
                      <div key={category.id} className="bw-table-row">
                        <div className="bw-table-cell">
                          <span className="bw-badge bw-badge-secondary" style={{ textTransform: 'capitalize' }}>
                            {category.vehicle_category}
                          </span>
                        </div>
                        <div className="bw-table-cell">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span>$</span>
                            <input
                              type="number"
                              min="0"
                              step="0.01"
                              value={currentRate}
                              className="bw-input"
                              style={{ width: '80px', padding: '4px 8px', fontSize: '14px' }}
                              data-category={category.vehicle_category}
                              onChange={(e) => {
                                const newRate = parseFloat(e.target.value) || 0
                                setEditingRates(prev => ({ ...prev, [category.vehicle_category]: newRate }))
                              }}
                              disabled={isSaving}
                            />
                          </div>
                        </div>
                        <div className="bw-table-cell">
                          <div className="bw-actions">
                            <button 
                              className="bw-btn-outline" 
                              style={{ fontSize: '12px', padding: '4px 8px' }}
                              disabled={isSaving}
                              onClick={() => {
                                const newRate = parseFloat(document.querySelector(`input[data-category="${category.vehicle_category}"]`)?.value || '0') || 0
                                if (newRate > 0) {
                                  saveVehicleRate(category.vehicle_category, newRate)
                                } else {
                                  alert('Please enter a valid rate greater than 0')
                                }
                              }}
                            >
                              {isSaving ? (
                                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                              ) : (
                                'Save'
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    )
                  })
                ) : (
                  // Empty state when no categories are available
                  <div className="bw-empty-state">
                    <div className="bw-empty-icon">
                      <Car className="w-8 h-8" />
                    </div>
                    <div className="bw-empty-text">No vehicle categories yet</div>
                    <div className="bw-empty-subtext">
                      Add your first vehicle category above to get started
                    </div>
                  </div>
                )}
              </div>
              
              <div style={{ marginTop: 16, padding: '16px', backgroundColor: '#f3f4f6', borderRadius: '4px' }}>
                <h5 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#374151' }}>How it works:</h5>
                <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '14px', color: '#6b7280' }}>
                  <li>These are default rates for new vehicles of each category</li>
                  <li>Individual vehicles can override these defaults</li>
                  <li>Changes apply to new vehicles, not existing ones</li>
                  <li>Rates are in USD and apply per ride</li>
                  <li>Add custom categories specific to your business needs</li>
                </ul>
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