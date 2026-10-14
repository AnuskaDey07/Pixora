import { api } from './client'

export interface ImageRecord {
  id: string
  filename: string | null
  width: number
  height: number
  mime: string
  size_bytes: number
  thumb_url: string | null
  original_url?: string
  nsfw_flagged?: boolean
  nsfw_score?: number | null
  created_at: string | null
}

export async function uploadImage(file: File): Promise<ImageRecord> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/images/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function listImages(limit = 40, offset = 0): Promise<{ images: ImageRecord[]; count: number }> {
  const { data } = await api.get('/images', { params: { limit, offset } })
  return data
}

export async function getImage(id: string): Promise<ImageRecord> {
  const { data } = await api.get(`/images/${id}`)
  return data
}

export async function deleteImage(id: string): Promise<void> {
  await api.delete(`/images/${id}`)
}
