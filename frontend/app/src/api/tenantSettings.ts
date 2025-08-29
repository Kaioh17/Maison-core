import { http } from './http'

export async function getTenantSettings() {
  const { data } = await http.get<TenantSettingsResponse>('/v1/tenant_setting/')
  return data
}

export async function updateTenantSettings(payload: UpdateTenantSetting) {
  const formData = new FormData()
  
  // Add all fields
  formData.append('theme', payload.theme)
  formData.append('slug', payload.slug)
  formData.append('enable_branding', payload.enable_branding.toString())
  formData.append('base_fare', payload.base_fare.toString())
  formData.append('per_minute_rate', payload.per_minute_rate.toString())
  formData.append('per_mile_rate', payload.per_mile_rate.toString())
  formData.append('per_hour_rate', payload.per_hour_rate.toString())
  formData.append('rider_tiers_enabled', payload.rider_tiers_enabled.toString())
  formData.append('cancellation_fee', payload.cancellation_fee.toString())
  formData.append('discounts', payload.discounts.toString())
  
  // Add logo file if provided
  if (payload.logo_url instanceof File) {
    formData.append('logo_url', payload.logo_url)
  } else if (typeof payload.logo_url === 'string') {
    formData.append('logo_url', payload.logo_url)
  }
  
  const { data } = await http.patch<TenantSettingsResponse>('/v1/tenant_setting/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function updateTenantLogo(logoFile: File) {
  try {
    const formData = new FormData()
    formData.append('logo_url', logoFile)
    
    console.log('Attempting to update logo with file:', logoFile.name, 'size:', logoFile.size)
    
    const response = await http.patch('/v1/tenant_setting/logo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    
    console.log('Logo update response:', response)
    
    // Return the response data directly, don't assume it's TenantSettingsResponse
    return response.data
  } catch (error) {
    console.error('Logo update failed:', error)
    if (error.response) {
      console.error('Response status:', error.response.status)
      console.error('Response data:', error.response.data)
    }
    throw error
  }
}

export async function updateTenantLogoOnly(logoFile: File) {
  try {
    const formData = new FormData()
    formData.append('logo_url', logoFile)
    
    const response = await http.patch('/v1/tenant_setting/logo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    
    // Return the response data directly, don't assume it's TenantSettingsResponse
    return response.data
  } catch (error) {
    console.error('Logo update failed:', error)
    throw error
  }
}

export async function testLogoEndpoint() {
  try {
    const response = await http.get('/v1/tenant_setting/logo')
    console.log('Logo endpoint test response:', response)
    return response
  } catch (error) {
    console.error('Logo endpoint test failed:', error)
    throw error
  }
}

export type TenantSettingsResponse = {
  id: number
  theme: string
  logo_url: string
  slug: string
  enable_branding: boolean
  base_fare: number
  per_minute_rate: number
  per_mile_rate: number
  per_hour_rate: number
  rider_tiers_enabled: boolean
  cancellation_fee: number
  discounts: boolean
  updated_on?: string | null
}

export type UpdateTenantSetting = {
  theme: string
  logo_url: string | File
  slug: string
  enable_branding: boolean
  base_fare: number
  per_minute_rate: number
  per_mile_rate: number
  per_hour_rate: number
  rider_tiers_enabled: boolean
  cancellation_fee: number
  discounts: boolean
} 