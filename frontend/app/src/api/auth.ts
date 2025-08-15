import { http } from './http'

export async function loginTenant(email: string, password: string) {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const { data } = await http.post('/v1/login/tenants', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data as { access_token: string }
}

export async function loginDriver(email: string, password: string) {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const { data } = await http.post('/v1/login/driver', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data as { access_token: string }
}

export async function loginRider(email: string, password: string) {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const { data } = await http.post('/v1/login/user', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data as { access_token: string }
}

export async function refreshTenantToken() {
  try {
    const { data } = await http.post('/v1/login/refresh_tenants')
    return data as { new_access_token: string }
  } catch (error) {
    throw error
  }
}

export async function refreshDriverToken() {
  try {
    const { data } = await http.post('/v1/login/refresh')
    return data as { new_access_token: string }
  } catch (error) {
    throw error
  }
}

export async function refreshRiderToken() {
  try {
    const { data } = await http.post('/v1/login/refresh')
    return data as { new_access_token: string }
  } catch (error) {
    throw error
  }
}

export async function checkAuthStatus() {
  try {
    // Try to make a request to check if the current token is valid
    const { data } = await http.get('/v1/tenants/me') // You'll need to create this endpoint
    return { isValid: true, user: data }
  } catch (error: any) {
    if (error.response?.status === 401) {
      return { isValid: false, user: null }
    }
    throw error
  }
} 