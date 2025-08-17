import { http } from './http'

export type StandardResponse<T> = {
  data: T
  message?: string
  meta?: Record<string, unknown>
  success?: boolean
}

export async function getTenantInfo() {
  const { data } = await http.get<StandardResponse<TenantResponse>>('/v1/tenant/')
  return data
}

export async function createTenant(payload: TenantCreate) {
  const { data } = await http.post<StandardResponse<TenantResponse>>('/v1/tenant/add', payload)
  return data
}

export async function getTenantDrivers() {
  const { data } = await http.get<StandardResponse<DriverResponse[]>>('/v1/tenant/drivers')
  return data
}

export async function getTenantVehicles(params?: { driver_id?: number; assigned_drivers?: boolean }) {
  const { data } = await http.get<StandardResponse<VehicleResponse[]>>('/v1/tenant/vehicles', { params })
  return data
}

export async function getTenantBookings(params?: { booking_status?: string }) {
  const { data } = await http.get<StandardResponse<BookingResponse[]>>('/v1/tenant/bookings', { params })
  return data
}

export async function onboardDriver(payload: OnboardDriver) {
  const { data } = await http.post<StandardResponse<OnboardDriverResponse>>('/v1/tenant/onboard', payload)
  return data
}

export async function assignDriverToRide(riderId: number, payload: AssignDriver) {
  const { data } = await http.patch(`/v1/tenant/riders/${riderId}/assign-driver`, payload)
  return data
}

export async function assignDriverToVehicle(vehicleId: number, payload: AssignDriver) {
  const { data } = await http.patch(`/v1/tenant/vehicles/${vehicleId}/assign-driver`, payload)
  return data
}

// Types aligned to backend
export type TenantCreate = {
  email: string
  first_name: string
  last_name: string
  password: string
  phone_no: string
  company_name: string
  logo_url?: string | null
  slug: string
  address?: string | null
  city: string
  drivers_count?: number
}
export type TenantResponse = {
  id: number
  email: string
  first_name: string
  last_name: string
  phone_no: string
  company_name: string
  logo_url?: string | null
  slug: string
  address?: string | null
  city: string
  role: string
  drivers_count: number
  is_verified: boolean
  is_active: boolean
  stripe_customer_id?: string | null
  stripe_account_id?: string | null
  subscription_status?: string | null
  subscription_plan?: string | null
  total_ride_count?: number | null
  daily_ride_count?: number | null
  last_ride_count_reset?: string | null
  created_on: string
  updated_on?: string | null
}

export type DriverResponse = {
  id: number
  email: string
  phone_no: string
  first_name: string
  last_name: string
  role: string
  driver_type: string
  completed_rides: number
  is_active: boolean
  status?: string | null
  created_on: string
  updated_on?: string | null
}

export type VehicleResponse = {
  id: number
  tenant_id: number
  make: string
  model: string
  year?: number
  license_plate?: string
  color?: string
  status?: string
  vehicle_config: {
    vehicle_category: string
    vehicle_flat_rate: number
    seating_capacity: number
  }
  created_on: string
  updated_on?: string | null
}

export type BookingResponse = {
  id: number
  tenant_id?: number
  city: string
  service_type: 'airport' | 'hourly' | 'dropoff'
  pickup_location: string
  pickup_time: string
  dropoff_location?: string | null
  dropoff_time?: string | null
  payment_method: 'cash' | 'card' | 'zelle'
  notes?: string | null
  estimated_price?: number
  booking_status: string
  created_on?: string
  updated_on?: string
}

export type OnboardDriver = {
  first_name: string
  last_name: string
  email: string
  driver_type: 'outsourced' | 'in_house'
}
export type OnboardDriverResponse = OnboardDriver & {
  id: number
  driver_token: string
  created_on: string
}

export type AssignDriver = { driver_id: number } 