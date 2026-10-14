import { api, setTokens, clearTokens } from './client'

export interface User {
  id: string
  email: string
  role: 'user' | 'admin'
  is_active?: boolean
  created_at?: string
}

export async function register(email: string, password: string): Promise<User> {
  const { data } = await api.post('/auth/register', { email, password })
  return data
}

export async function login(email: string, password: string): Promise<User> {
  const { data } = await api.post('/auth/login', { email, password })
  setTokens(data.access_token, data.refresh_token)
  return data.user
}

export async function me(): Promise<User> {
  const { data } = await api.get('/auth/me')
  return data
}

export function logout() {
  clearTokens()
}
