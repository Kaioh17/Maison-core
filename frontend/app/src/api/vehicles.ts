import { http } from './http'

export async function getVehicles() {
  const { data } = await http.get<VehicleResponse[]>('/v1/vehicles/')
  return data
}

export async function addVehicle(payload: VehicleCreate) {
  const { data } = await http.post<VehicleResponse>('/v1/vehicles/add', payload)
  return data
}

export async function setVehicleRates(payload: VehicleRate) {
  const { data } = await http.patch<VehicleCategoryRateResponse>('/v1/vehicles/set_rates', payload)
  return data
}

export async function getVehicleRates() {
  const { data } = await http.get<VehicleCategoryRateResponse[]>('/v1/vehicles/vehicle_rates')
  return data
}

export async function getVehicleCategories() {
  const { data } = await http.get<VehicleCategoryResponse[]>('/v1/vehicles/category')
  return data
}

export async function createVehicleCategory(payload: VehicleCategoryCreate) {
  const { data } = await http.post<VehicleCategoryResponse>('/v1/vehicles/create_category', payload)
  return data
}

export type VehicleCreate = {
  make: string
  model: string
  year?: number
  license_plate?: string
  color?: string
  status?: string
  vehicle_category: string
  vehicle_flat_rate: number
  seating_capacity: number
}

export type VehicleResponse = {
  tenant_id: number
  id: number
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

export type VehicleRate = {
  vehicle_category: string
  vehicle_flat_rate: number
}

export type VehicleCategoryRateResponse = {
  id: number
  tenant_id: number
  vehicle_category: string
  vehicle_flat_rate: number
  created_on: string
  updated_on?: string | null
}

export type VehicleCategoryRateCreate = VehicleRate 

export type VehicleCategoryCreate = {
  vehicle_category: string
  vehicle_flat_rate: number
  seating_capacity: number
}

export type VehicleCategoryResponse = {
  id: number
  tenant_id: number
  vehicle_category: string
  vehicle_flat_rate: number
  created_on: string
  updated_on?: string | null
} 