import { api } from './client'

export type JobStatus = 'pending' | 'running' | 'done' | 'failed' | 'timeout'

export interface Job {
  id: string
  type: string
  status: JobStatus
  image_id: string | null
  params: Record<string, unknown>
  meta: Record<string, unknown>
  result_url: string | null
  error: string | null
  created_at: string | null
  started_at: string | null
  finished_at: string | null
}

export interface CreateJobPayload {
  type: string
  image_id?: string
  params?: Record<string, unknown>
}

export async function createJob(payload: CreateJobPayload): Promise<Job> {
  const { data } = await api.post('/jobs', payload)
  return data
}

export async function getJob(id: string): Promise<Job> {
  const { data } = await api.get(`/jobs/${id}`)
  return data
}

export async function listJobs(params?: { status?: string; type?: string; limit?: number; offset?: number }): Promise<{ jobs: Job[]; count: number }> {
  const { data } = await api.get('/jobs', { params })
  return data
}
