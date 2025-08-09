export const API_BASE = import.meta.env.VITE_API_BASE ?? '';

export type UserRole = 'tenant' | 'driver' | 'rider' | 'admin';

export const REFRESH_ENDPOINT_BY_ROLE: Record<UserRole, string> = {
  tenant: '/v1/login/refresh_tenants',
  driver: '/v1/login/refresh',
  rider: '/v1/login/refresh',
  admin: '/v1/login/refresh',
}; 