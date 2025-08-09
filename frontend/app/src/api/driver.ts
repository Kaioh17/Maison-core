import { http } from './http'
import type { StandardResponse, BookingResponse } from './tenant'

export async function registerDriver(payload: DriverCreate) {
  const { data } = await http.patch<StandardResponse<DriverResponse>>('/v1/driver/register', payload)
  return data
}

export async function getDriverInfo() {
  const { data } = await http.get<StandardResponse<DriverResponse>>('/v1/driver/info')
  return data
}

export async function getAvailableRides(booking_status = 'pending') {
  const { data } = await http.get<StandardResponse<BookingResponse[]>>('/v1/driver/rides/available', {
    params: { booking_status },
  })
  return data
}

export async function respondToRide(bookingId: number, action: 'confirm' | 'cancelled') {
  const { data } = await http.patch<StandardResponse<BookingResponse>>(`/v1/driver/ride/${bookingId}/decision`, null, {
    params: { action },
  })
  return data
}

export type DriverCreate = {
  email: string
  phone_no: string
  first_name: string
  last_name: string
  driver_token: string
  password: string
  state?: string
  postal_code?: string
  license_number?: string
  vehicle?: {
    make: string
    model: string
    year?: number
    license_plate?: string
    color?: string
  }
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
  vehicle?: {
    make: string
    model: string
    year?: number
    license_plate?: string
    color?: string
  } | null
} 