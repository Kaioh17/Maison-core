import { http } from './http'
import type { StandardResponse, TenantResponse } from './tenant'

export async function getTenants() {
  const { data } = await http.get<StandardResponse<TenantResponse[]>>('/v1/admin/tenants')
  return data
}

export async function deleteTenant(tenantId: number) {
  const { data } = await http.delete(`/v1/admin/delete/${tenantId}/tenant`)
  return data
} 