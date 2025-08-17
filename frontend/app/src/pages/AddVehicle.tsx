import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Car, ArrowLeft, Plus, XCircle } from 'lucide-react'
import { addVehicle, getVehicleCategories } from '@api/vehicles'
import { useAuthStore } from '@store/auth'

export default function AddVehicle() {
  const [formData, setFormData] = useState({
    make: '',
    model: '',
    year: '',
    license_plate: '',
    color: '',
    status: 'available',
    vehicle_category: '',
    vehicle_flat_rate: '',
    seating_capacity: 4
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [vehicleCategories, setVehicleCategories] = useState<any[]>([])
  const [loadingCategories, setLoadingCategories] = useState(true)
  const [customFields, setCustomFields] = useState<Array<{ key: string; value: string }>>([])
  const [showAddField, setShowAddField] = useState(false)
  const [newFieldKey, setNewFieldKey] = useState('')
  const [newFieldValue, setNewFieldValue] = useState('')
  
  const navigate = useNavigate()
  const { role } = useAuthStore()

  // Fetch vehicle categories on component mount
  useEffect(() => {
    const loadVehicleCategories = async () => {
      try {
        setLoadingCategories(true)
        const categories = await getVehicleCategories()
        setVehicleCategories(categories || [])
        
        // Set default category if available
        if (categories && categories.length > 0) {
          setFormData(prev => ({
            ...prev,
            vehicle_category: categories[0].vehicle_category,
            vehicle_flat_rate: categories[0].vehicle_flat_rate.toString()
          }))
        }
      } catch (error) {
        console.error('Failed to load vehicle categories:', error)
      } finally {
        setLoadingCategories(false)
      }
    }

    loadVehicleCategories()
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    
    // If vehicle category is selected, automatically populate the base rate
    if (name === 'vehicle_category') {
      const selectedCategory = vehicleCategories.find(cat => cat.vehicle_category === value)
      if (selectedCategory) {
        setFormData(prev => ({
          ...prev,
          [name]: value,
          vehicle_flat_rate: selectedCategory.vehicle_flat_rate.toString()
        }))
        return
      }
    }
    
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.make || !formData.model) {
      setError('Make and Model are required fields')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      // Prepare the payload according to the backend schema
      const vehiclePayload = {
        make: formData.make,
        model: formData.model,
        year: formData.year ? parseInt(formData.year) : undefined,
        license_plate: formData.license_plate || undefined,
        color: formData.color || undefined,
        status: formData.status,
        vehicle_category: formData.vehicle_category,
        vehicle_flat_rate: parseFloat(formData.vehicle_flat_rate) || 0,
        seating_capacity: parseInt(formData.seating_capacity.toString()) || 4,
        // Add custom fields as metadata
        metadata: customFields.reduce((acc, field) => {
          acc[field.key] = field.value
          return acc
        }, {} as Record<string, string>)
      }

      await addVehicle(vehiclePayload)
      setSuccess(true)
      
      // Redirect to dashboard after a short delay
      setTimeout(() => {
        navigate('/tenant')
      }, 2000)
      
    } catch (err: any) {
      console.error('Failed to create vehicle:', err)
      setError(err.response?.data?.detail || 'Failed to create vehicle. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleBack = () => {
    navigate('/tenant')
  }

  // Custom field management functions
  const addCustomField = () => {
    if (newFieldKey.trim() && newFieldValue.trim()) {
      setCustomFields(prev => [...prev, { key: newFieldKey.trim(), value: newFieldValue.trim() }])
      setNewFieldKey('')
      setNewFieldValue('')
      setShowAddField(false)
    }
  }

  const removeCustomField = (index: number) => {
    setCustomFields(prev => prev.filter((_, i) => i !== index))
  }

  const editCustomField = (index: number, key: string, value: string) => {
    setCustomFields(prev => prev.map((field, i) => 
      i === index ? { key, value } : field
    ))
  }

  const toggleAddField = () => {
    setShowAddField(!showAddField)
    if (!showAddField) {
      setNewFieldKey('')
      setNewFieldValue('')
    }
  }

  if (success) {
    return (
      <div className="bw bw-container" style={{ padding: '24px 0' }}>
        <div className="bw-card" style={{ textAlign: 'center', padding: '48px 24px' }}>
          <div style={{ color: '#10b981', marginBottom: '16px' }}>
            <Car className="w-12 h-12 mx-auto" />
          </div>
          <h3 style={{ margin: '0 0 16px 0', color: '#10b981' }}>Vehicle Created Successfully!</h3>
          <p style={{ margin: '0 0 24px 0', color: '#6b7280' }}>
            Your new vehicle has been added to your fleet. Redirecting to dashboard...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bw bw-container" style={{ padding: '24px 0' }}>
      {/* Header */}
      <div className="bw-header" style={{ marginBottom: 32 }}>
        <div className="bw-header-content">
          <button 
            className="bw-btn-outline" 
            onClick={handleBack}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </button>
          <h1 style={{ fontSize: 32, margin: '0 0 0 24px' }}>Add New Vehicle</h1>
        </div>
      </div>

      {/* Form */}
      <div className="bw-card" style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div className="bw-card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ 
              width: 40, 
              height: 40, 
              border: '1px solid var(--bw-border-strong)', 
              display: 'grid', 
              placeItems: 'center', 
              borderRadius: 2 
            }}>
              <Car size={20} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 20 }}>Vehicle Information</h3>
              <p className="small-muted" style={{ margin: '4px 0 0 0' }}>
                Add a new vehicle to your fleet
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '24px' }}>
          {error && (
            <div style={{ 
              marginBottom: 24, 
              padding: '12px', 
              backgroundColor: '#fee2e2', 
              border: '1px solid #fecaca', 
              borderRadius: '4px',
              color: '#dc2626',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          {/* Basic Vehicle Information */}
          <div style={{ marginBottom: 32 }}>
            <h4 style={{ margin: '0 0 16px 0', fontSize: 16, fontWeight: 600 }}>Basic Information</h4>
            <div className="bw-form-grid" style={{ display: 'grid', gap: '16px', gridTemplateColumns: '1fr 1fr' }}>
              <div className="bw-form-group">
                <label className="bw-form-label">Make *</label>
                <input 
                  className="bw-input" 
                  name="make"
                  value={formData.make} 
                  onChange={handleInputChange} 
                  placeholder="Escalade"
                  required
                  style={{
                    color: 'var(--bw-fg)',
                    backgroundColor: 'var(--bw-bg)',
                    border: '1px solid var(--bw-border)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '14px',
                    width: '100%',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer'
                  }}
                  onFocus={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                    ;(e.target as HTMLInputElement).style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1.02)'
                  }}
                  onBlur={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                    ;(e.target as HTMLInputElement).style.boxShadow = 'none'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1)'
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                  }}
                />
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Model *</label>
                <input 
                  className="bw-input" 
                  name="model"
                  value={formData.model} 
                  onChange={handleInputChange} 
                  placeholder="Camry"
                  required
                  style={{
                    color: 'var(--bw-fg)',
                    backgroundColor: 'var(--bw-bg)',
                    border: '1px solid var(--bw-border)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '14px',
                    width: '100%',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer'
                  }}
                  onFocus={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                    ;(e.target as HTMLInputElement).style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1.02)'
                  }}
                  onBlur={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                    ;(e.target as HTMLInputElement).style.boxShadow = 'none'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1)'
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                  }}
                />
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Year</label>
                <input 
                  className="bw-input" 
                  type="number" 
                  name="year"
                  min="1900" 
                  max={new Date().getFullYear() + 1}
                  value={formData.year} 
                  onChange={handleInputChange} 
                  placeholder="2024"
                  style={{
                    color: 'var(--bw-fg)',
                    backgroundColor: 'var(--bw-bg)',
                    border: '1px solid var(--bw-border)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '14px',
                    width: '100%',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer'
                  }}
                  onFocus={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                    ;(e.target as HTMLInputElement).style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1.02)'
                  }}
                  onBlur={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                    ;(e.target as HTMLInputElement).style.boxShadow = 'none'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1)'
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                  }}
                />
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Color</label>
                <input 
                  className="bw-input" 
                  name="color"
                  value={formData.color} 
                  onChange={handleInputChange} 
                  placeholder="Black"
                  style={{
                    color: 'var(--bw-fg)',
                    backgroundColor: 'var(--bw-bg)',
                    border: '1px solid var(--bw-border)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '14px',
                    width: '100%',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer'
                  }}
                  onFocus={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                    ;(e.target as HTMLInputElement).style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1.02)'
                  }}
                  onBlur={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                    ;(e.target as HTMLInputElement).style.boxShadow = 'none'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1)'
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                  }}
                />
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">License Plate</label>
                <input 
                  className="bw-input" 
                  name="license_plate"
                  value={formData.license_plate} 
                  onChange={handleInputChange} 
                  placeholder="ABC-123"
                  style={{
                    color: 'var(--bw-fg)',
                    backgroundColor: 'var(--bw-bg)',
                    border: '1px solid var(--bw-border)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '14px',
                    width: '100%',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer'
                  }}
                  onFocus={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                    ;(e.target as HTMLInputElement).style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1.02)'
                  }}
                  onBlur={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                    ;(e.target as HTMLInputElement).style.boxShadow = 'none'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1)'
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                  }}
                />
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Status</label>
                <select 
                  className="bw-input" 
                  name="status"
                  value={formData.status} 
                  onChange={handleInputChange}
                  style={{
                    color: 'var(--bw-fg)',
                    backgroundColor: 'var(--bw-bg)',
                    border: '1px solid var(--bw-border)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '14px',
                    width: '100%',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer'
                  }}
                  onFocus={(e) => {
                    (e.target as HTMLSelectElement).style.borderColor = 'var(--bw-accent)'
                    ;(e.target as HTMLSelectElement).style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
                    ;(e.target as HTMLSelectElement).style.transform = 'scale(1.02)'
                  }}
                  onBlur={(e) => {
                    (e.target as HTMLSelectElement).style.borderColor = 'var(--bw-border)'
                    ;(e.target as HTMLSelectElement).style.boxShadow = 'none'
                    ;(e.target as HTMLSelectElement).style.transform = 'scale(1)'
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLSelectElement).style.borderColor = 'var(--bw-accent)'
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLSelectElement).style.borderColor = 'var(--bw-border)'
                  }}
                >
                  <option value="available" style={{ color: 'var(--bw-fg)', backgroundColor: 'var(--bw-bg)' }}>Available</option>
                  <option value="maintenance" style={{ color: 'var(--bw-fg)', backgroundColor: 'var(--bw-bg)' }}>Maintenance</option>
                  <option value="out_of_service" style={{ color: 'var(--bw-fg)', backgroundColor: 'var(--bw-bg)' }}>Out of Service</option>
                </select>
              </div>
            </div>
          </div>

          {/* Vehicle Configuration */}
          <div style={{ marginBottom: 32 }}>
            <h4 style={{ margin: '0 0 16px 0', fontSize: 16, fontWeight: 600 }}>Vehicle Configuration</h4>
            <div className="bw-form-grid" style={{ display: 'grid', gap: '16px', gridTemplateColumns: '1fr 1fr' }}>
              <div className="bw-form-group">
                <label className="bw-form-label">Vehicle Category</label>
                <select 
                  className="bw-input" 
                  name="vehicle_category"
                  value={formData.vehicle_category} 
                  onChange={handleInputChange}
                  style={{
                    color: 'var(--bw-fg)',
                    backgroundColor: 'var(--bw-bg)',
                    border: '1px solid var(--bw-border)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '14px',
                    width: '100%',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer'
                  }}
                  onFocus={(e) => {
                    (e.target as HTMLSelectElement).style.borderColor = 'var(--bw-accent)'
                    ;(e.target as HTMLSelectElement).style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
                    ;(e.target as HTMLSelectElement).style.transform = 'scale(1.02)'
                  }}
                  onBlur={(e) => {
                    (e.target as HTMLSelectElement).style.borderColor = 'var(--bw-border)'
                    ;(e.target as HTMLSelectElement).style.boxShadow = 'none'
                    ;(e.target as HTMLSelectElement).style.transform = 'scale(1)'
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLSelectElement).style.borderColor = 'var(--bw-accent)'
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLSelectElement).style.borderColor = 'var(--bw-border)'
                  }}
                >
                  {loadingCategories ? (
                    <option value="" style={{ color: 'var(--bw-fg)', backgroundColor: 'var(--bw-bg)' }}>Loading categories...</option>
                  ) : vehicleCategories.length === 0 ? (
                    <option value="" style={{ color: 'var(--bw-fg)', backgroundColor: 'var(--bw-bg)' }}>No categories available</option>
                  ) : (
                    vehicleCategories.map(category => (
                      <option key={category.id} value={category.vehicle_category} style={{ color: 'var(--bw-fg)', backgroundColor: 'var(--bw-bg)' }}>
                        {category.vehicle_category}
                      </option>
                    ))
                  )}
                </select>
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Seating Capacity</label>
                <input 
                  className="bw-input" 
                  type="number" 
                  name="seating_capacity"
                  min="1" 
                  max="20"
                  value={formData.seating_capacity} 
                  onChange={handleInputChange} 
                  style={{
                    color: 'var(--bw-fg)',
                    backgroundColor: 'var(--bw-bg)',
                    border: '1px solid var(--bw-border)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '14px',
                    width: '100%',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer'
                  }}
                  onFocus={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                    ;(e.target as HTMLInputElement).style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1.02)'
                  }}
                  onBlur={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                    ;(e.target as HTMLInputElement).style.boxShadow = 'none'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1)'
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                  }}
                />
              </div>
              <div className="bw-form-group">
                <label className="bw-form-label">Base Rate ($)</label>
                <input 
                  className="bw-input" 
                  type="number" 
                  name="vehicle_flat_rate"
                  min="0" 
                  step="0.01"
                  value={formData.vehicle_flat_rate} 
                  onChange={handleInputChange} 
                  placeholder="25.00"
                  style={{
                    color: 'var(--bw-fg)',
                    backgroundColor: 'var(--bw-bg)',
                    border: '1px solid var(--bw-border)',
                    borderRadius: '6px',
                    padding: '10px 12px',
                    fontSize: '14px',
                    width: '100%',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer'
                  }}
                  onFocus={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                    ;(e.target as HTMLInputElement).style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1.02)'
                  }}
                  onBlur={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                    ;(e.target as HTMLInputElement).style.boxShadow = 'none'
                    ;(e.target as HTMLInputElement).style.transform = 'scale(1)'
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-accent)'
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLInputElement).style.borderColor = 'var(--bw-border)'
                  }}
                />
              </div>
            </div>
          </div>

          {/* Custom Fields Section */}
          <div style={{ marginBottom: 32 }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              marginBottom: '16px' 
            }}>
              <h4 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Additional Information</h4>
              <button
                type="button"
                className="bw-btn-outline"
                onClick={toggleAddField}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '14px',
                  padding: '8px 16px'
                }}
              >
                <Plus className="w-4 h-4" />
                {showAddField ? 'Cancel' : 'Add Field'}
              </button>
            </div>

            {/* Add New Field Form */}
            {showAddField && (
              <div style={{
                padding: '16px',
                border: '1px solid var(--bw-border)',
                borderRadius: '8px',
                backgroundColor: 'var(--bw-bg-hover)',
                marginBottom: '16px'
              }}>
                <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: '1fr 1fr auto' }}>
                  <div className="bw-form-group">
                    <label style={{ 
                      fontSize: '14px', 
                      fontWeight: '500', 
                      color: 'var(--bw-fg)',
                      marginBottom: '6px',
                      display: 'block'
                    }}>
                      Field Name
                    </label>
                    <input
                      type="text"
                      value={newFieldKey}
                      onChange={(e) => setNewFieldKey(e.target.value)}
                      placeholder="e.g., Engine Size, Fuel Type"
                      style={{
                        color: 'var(--bw-fg)',
                        backgroundColor: 'var(--bw-bg)',
                        border: '1px solid var(--bw-border)',
                        borderRadius: '6px',
                        padding: '10px 12px',
                        fontSize: '14px',
                        width: '100%',
                        transition: 'all 0.2s ease'
                      }}
                    />
                  </div>
                  <div className="bw-form-group">
                    <label style={{ 
                      fontSize: '14px', 
                      fontWeight: '500', 
                      color: 'var(--bw-fg)',
                      marginBottom: '6px',
                      display: 'block'
                    }}>
                      Field Value
                    </label>
                    <input
                      type="text"
                      value={newFieldValue}
                      onChange={(e) => setNewFieldValue(e.target.value)}
                      placeholder="e.g., 2.0L, Gasoline"
                      style={{
                        color: 'var(--bw-fg)',
                        backgroundColor: 'var(--bw-bg)',
                        border: '1px solid var(--bw-border)',
                        borderRadius: '6px',
                        padding: '10px 12px',
                        fontSize: '14px',
                        width: '100%',
                        transition: 'all 0.2s ease'
                      }}
                    />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'end', gap: '8px' }}>
                    <button
                      type="button"
                      className="bw-btn"
                      onClick={addCustomField}
                      disabled={!newFieldKey.trim() || !newFieldValue.trim()}
                      style={{
                        padding: '10px 16px',
                        fontSize: '14px',
                        color: '#000'
                      }}
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Display Custom Fields */}
            {customFields.length > 0 && (
              <div style={{ display: 'grid', gap: '12px' }}>
                {customFields.map((field, index) => (
                  <div key={index} style={{
                    display: 'grid',
                    gap: '16px',
                    gridTemplateColumns: '1fr 1fr auto',
                    padding: '16px',
                    border: '1px solid var(--bw-border)',
                    borderRadius: '8px',
                    backgroundColor: 'var(--bw-bg)',
                    alignItems: 'center'
                  }}>
                    <input
                      type="text"
                      value={field.key}
                      onChange={(e) => editCustomField(index, e.target.value, field.value)}
                      placeholder="Field Name"
                      style={{
                        color: 'var(--bw-fg)',
                        backgroundColor: 'var(--bw-bg-hover)',
                        border: '1px solid var(--bw-border)',
                        borderRadius: '6px',
                        padding: '10px 12px',
                        fontSize: '14px',
                        width: '100%',
                        transition: 'all 0.2s ease'
                      }}
                    />
                    <input
                      type="text"
                      value={field.value}
                      onChange={(e) => editCustomField(index, field.key, e.target.value)}
                      placeholder="Field Value"
                      style={{
                        color: 'var(--bw-fg)',
                        backgroundColor: 'var(--bw-bg-hover)',
                        border: '1px solid var(--bw-border)',
                        borderRadius: '6px',
                        padding: '10px 12px',
                        fontSize: '14px',
                        width: '100%',
                        transition: 'all 0.2s ease'
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => removeCustomField(index)}
                      style={{
                        padding: '8px',
                        border: '1px solid #ef4444',
                        backgroundColor: 'transparent',
                        color: '#ef4444',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = '#ef4444'
                        e.currentTarget.style.color = 'white'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent'
                        e.currentTarget.style.color = '#ef4444'
                      }}
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Empty State for Custom Fields */}
            {customFields.length === 0 && !showAddField && (
              <div style={{
                padding: '24px',
                border: '1px dashed var(--bw-border)',
                borderRadius: '8px',
                textAlign: 'center',
                color: 'var(--bw-muted)',
                backgroundColor: 'var(--bw-bg-hover)'
              }}>
                <div style={{ marginBottom: '8px' }}>
                  <Plus className="w-6 h-6 mx-auto" />
                </div>
                <p style={{ margin: '0 0 8px 0', fontSize: '14px' }}>
                  No additional fields added yet
                </p>
                <p style={{ margin: 0, fontSize: '12px' }}>
                  Click "Add Field" to include custom vehicle information
                </p>
              </div>
            )}
          </div>

          {/* Form Actions */}
          <div style={{ 
            display: 'flex', 
            gap: '16px', 
            justifyContent: 'flex-end', 
            borderTop: '1px solid var(--bw-border)', 
            paddingTop: '24px' 
          }}>
            <button 
              type="button" 
              className="bw-btn-outline" 
              onClick={handleBack}
              disabled={isLoading}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="bw-btn" 
              disabled={isLoading}
              style={{ color: '#000' }}
            >
              {isLoading ? (
                <>
                  <div className="bw-loading-spinner" style={{ width: '16px', height: '16px' }}></div>
                  Creating Vehicle...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  Add Vehicle
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
} 