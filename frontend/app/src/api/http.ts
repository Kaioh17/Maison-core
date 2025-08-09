import axios from 'axios'
import { API_BASE, REFRESH_ENDPOINT_BY_ROLE } from '@config'
import { useAuthStore } from '@store/auth'

export const http = axios.create({
  baseURL: API_BASE,
  withCredentials: true, // to send/receive refresh_token cookie
})

http.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let pendingQueue: Array<() => void> = []

function onRefreshed() {
  pendingQueue.forEach((cb) => cb())
  pendingQueue = []
}

http.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    const status = error?.response?.status
    if (status === 401 && !original._retry) {
      original._retry = true

      const store = useAuthStore.getState()
      if (isRefreshing) {
        await new Promise<void>((resolve) => pendingQueue.push(resolve))
      } else {
        try {
          isRefreshing = true
          const refreshPath = REFRESH_ENDPOINT_BY_ROLE[store.role || 'rider']
          const resp = await http.post(refreshPath)
          const newToken = resp.data?.new_access_token
          if (newToken) useAuthStore.getState().setAccessToken(newToken)
        } catch (err) {
          useAuthStore.getState().logout()
          return Promise.reject(error)
        } finally {
          isRefreshing = false
          onRefreshed()
        }
      }

      original.headers = original.headers || {}
      original.headers.Authorization = `Bearer ${useAuthStore.getState().accessToken}`
      return http(original)
    }

    return Promise.reject(error)
  }
) 