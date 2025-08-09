import { http } from './http'
import type { BookingResponse } from './tenant'

export async function createBooking(payload: CreateBooking) {
  const { data } = await http.post<BookingResponse>('/v1/bookings/set', payload)
  return data
}

export async function getMyBookings() {
  const { data } = await http.get<BookingResponse[]>('/v1/bookings/')
  return data
}

export type CreateBooking = {
  vehicle_id?: number
  city: string
  service_type: 'airport' | 'hourly' | 'dropoff'
  pickup_location: string
  pickup_time: string
  dropoff_location?: string
  dropoff_time?: string
  payment_method: 'cash' | 'card' | 'zelle'
  notes?: string
} 