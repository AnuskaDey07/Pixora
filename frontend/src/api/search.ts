import { api } from './client'

export interface SearchResult {
  image_id: string
  filename: string | null
  score: number
  thumb_url: string | null
}

export interface SearchResponse {
  query?: string
  reference_id?: string
  results: SearchResult[]
  count: number
}

export async function semanticSearch(query: string, limit = 20): Promise<SearchResponse> {
  const { data } = await api.post('/search/semantic', { query, limit })
  return data
}

export async function similarSearch(imageId: string, limit = 20): Promise<SearchResponse> {
  const { data } = await api.post('/search/similar', { image_id: imageId, limit })
  return data
}
