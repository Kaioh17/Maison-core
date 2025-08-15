import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { API_BASE, REFRESH_ENDPOINT_BY_ROLE, UserRole } from '@config'
import { useAuthStore } from '@store/auth'

function resolveApiBase(): string {
	try {
		if (API_BASE.startsWith('http://') || API_BASE.startsWith('https://')) {
			const url = new URL(API_BASE, typeof window !== 'undefined' ? window.location.href : undefined)
			if ((url.hostname === '127.0.0.1' || url.hostname === 'localhost') && !url.port) {
				url.port = '8000'
			}
			return url.origin + url.pathname.replace(/\/$/, '')
		}
		return API_BASE
	} catch {
		return API_BASE
	}
}

const RESOLVED_BASE = resolveApiBase()

export const http = axios.create({
	baseURL: RESOLVED_BASE,
	withCredentials: true, // to send/receive refresh_token cookie
	maxRedirects: 5, // Allow following redirects (e.g., /api/v1/tenant -> /api/v1/tenant/)
})

http.interceptors.request.use((config: AxiosRequestConfig) => {
	const token = useAuthStore.getState().accessToken
	console.log('🚀 HTTP Request:', {
		method: config.method?.toUpperCase(),
		url: config.url,
		baseURL: config.baseURL,
		resolvedBaseURL: RESOLVED_BASE,
		fullURL: `${config.baseURL}${config.url}`,
		hasToken: !!token
	})
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
	(res: AxiosResponse) => {
		console.log('✅ HTTP Response:', {
			status: res.status,
			url: res.config.url,
			data: res.data
		})
		return res
	},
	async (error: AxiosError) => {
		console.error('❌ HTTP Error:', {
			status: error?.response?.status,
			url: error?.config?.url,
			message: error?.message,
			response: error?.response?.data
		})
		
		const original = error.config
		const status = error?.response?.status
		
		if (status === 401 && original && !(original as any)._retry) {
			(original as any)._retry = true

			const store = useAuthStore.getState()
			
			if (isRefreshing) {
				await new Promise<void>((resolve) => pendingQueue.push(resolve))
			} else {
				try {
					isRefreshing = true
					
					// Only attempt refresh if we have a role
					if (store.role) {
						const refreshPath = REFRESH_ENDPOINT_BY_ROLE[store.role as UserRole]
						const resp = await http.post(refreshPath)
						const newToken = resp.data?.new_access_token
						
						if (newToken) {
							store.setAccessToken(newToken)
						} else {
							throw new Error('No new token received')
						}
					} else {
						throw new Error('No role available for refresh')
					}
				} catch (err) {
					console.error('Token refresh failed:', err)
					store.logout()
					return Promise.reject(error)
				} finally {
					isRefreshing = false
					onRefreshed()
				}
			}

			// Retry the original request with new token
			const newToken = useAuthStore.getState().accessToken
			if (newToken && original) {
				original.headers = original.headers || {}
				original.headers.Authorization = `Bearer ${newToken}`
				return http(original)
			} else {
				return Promise.reject(error)
			}
		}

		return Promise.reject(error)
	}
) 