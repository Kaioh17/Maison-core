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
	withCredentials: true,
	maxRedirects: 5,
})

http.interceptors.request.use((config: AxiosRequestConfig) => {
	const token = useAuthStore.getState().accessToken
	if (token) {
		config.headers = config.headers || {}
		config.headers.Authorization = `Bearer ${token}`
	}
	return config
})

let isRefreshing = false
let pendingQueue: Array<() => void> = []

async function performTokenRefresh(): Promise<string> {
	const store = useAuthStore.getState()
	
	if (!store.role) {
		throw new Error('No role available for refresh')
	}
	
	const refreshPath = REFRESH_ENDPOINT_BY_ROLE[store.role as UserRole]
	
	const resp = await http.post(refreshPath)
	const newToken = resp.data?.new_access_token
	
	if (newToken) {
		store.setAccessToken(newToken)
		return newToken
	} else {
		throw new Error('No new token received')
	}
}

function onRefreshed() {
	pendingQueue.forEach((cb) => cb())
	pendingQueue = []
}

http.interceptors.response.use(
	(res: AxiosResponse) => res,
	async (error: AxiosError) => {
		const original = error.config
		const status = error?.response?.status
		
		if (status === 401 && original && !(original as any)._retry) {
			(original as any)._retry = true

			if (isRefreshing) {
				await new Promise<void>((resolve) => pendingQueue.push(resolve))
			} else {
				try {
					isRefreshing = true
					await performTokenRefresh()
				} catch (err) {
					useAuthStore.getState().logout()
					return Promise.reject(error)
				} finally {
					isRefreshing = false
					onRefreshed()
				}
			}

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