import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

export const TOKEN_KEY = 'pixora.access_token'
export const REFRESH_KEY = 'pixora.refresh_token'

export const api = axios.create({
  baseURL: '/api',
  timeout: 30_000,
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// --- Silent Refresh Logic ---
let isRefreshing = false
let failedQueue: any[] = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // If it's a 401 and we haven't already tried to retry this request
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If a refresh is already in progress, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = localStorage.getItem(REFRESH_KEY)
      if (!refreshToken) {
        // No refresh token, force logout
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        // Call the refresh endpoint
        const { data } = await axios.post('/api/auth/refresh', { refresh_token: refreshToken })
        
        // Save the new access token
        localStorage.setItem(TOKEN_KEY, data.access_token)
        
        // Update the header for the original request
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        
        // Process any queued requests
        processQueue(null, data.access_token)
        
        // Retry the original request
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed (e.g., refresh token expired), force logout
        processQueue(refreshError, null)
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export function setTokens(access: string, refresh?: string) {
  localStorage.setItem(TOKEN_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function hasToken(): boolean {
  return !!localStorage.getItem(TOKEN_KEY)
}