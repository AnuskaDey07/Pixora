import { api } from './client'

export interface AdminUser {
  id: string
  email: string
  role: 'user' | 'admin'
  is_active: boolean
  created_at: string | null
  disabled_at: string | null
}

export interface NsfwQueueItem {
  id: string
  user_id: string
  filename: string | null
  nsfw_score: number | null
  thumb_url: string | null
  original_url: string
  created_at: string | null
}

export async function listUsers(): Promise<{ users: AdminUser[]; count: number }> {
  const { data } = await api.get('/admin/users')
  return data
}

export async function updateUser(id: string, patch: { is_active?: boolean; role?: 'user' | 'admin' }): Promise<AdminUser> {
  const { data } = await api.patch(`/admin/users/${id}`, patch)
  return data
}

export async function listAllJobs(limit = 50): Promise<{ jobs: any[]; count: number }> {
  const { data } = await api.get('/admin/jobs', { params: { limit } })
  return data
}

export async function nsfwQueue(): Promise<{ images: NsfwQueueItem[]; count: number }> {
  const { data } = await api.get('/admin/nsfw-queue')
  return data
}

export async function approveNsfw(imageId: string): Promise<void> {
  await api.post(`/admin/nsfw-queue/${imageId}/approve`)
}

export async function rejectNsfw(imageId: string): Promise<void> {
  await api.post(`/admin/nsfw-queue/${imageId}/reject`)
}
