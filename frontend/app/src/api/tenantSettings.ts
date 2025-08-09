import { http } from './http'

export async function updateTenantSettings(payload: UpdateTenantSetting) {
  const { data } = await http.patch<UpdateTenantSetting>('/api/v1/tenant_setting/', payload)
  return data
}

export type UpdateTenantSetting = {
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
} 