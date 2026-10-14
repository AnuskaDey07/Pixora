import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as jobsApi from '@/api/jobs'
import type { Job, CreateJobPayload } from '@/api/jobs'

export const useJobsStore = defineStore('jobs', () => {
  const items = ref<Job[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function refresh(params?: { status?: string; type?: string; limit?: number; offset?: number }) {
    loading.value = true
    error.value = null
    try {
      const res = await jobsApi.listJobs(params)
      items.value = res.jobs
    } catch (e: any) {
      error.value = e?.response?.data?.error ?? 'load_failed'
    } finally {
      loading.value = false
    }
  }

  async function create(payload: CreateJobPayload): Promise<Job> {
    const job = await jobsApi.createJob(payload)
    items.value = [job, ...items.value]
    return job
  }

  async function poll(jobId: string, intervalMs = 2000, timeoutMs = 300_000): Promise<Job> {
    const start = Date.now()
    while (Date.now() - start < timeoutMs) {
      const job = await jobsApi.getJob(jobId)
      const idx = items.value.findIndex((j) => j.id === job.id)
      if (idx >= 0) items.value[idx] = job
      if (job.status === 'done' || job.status === 'failed' || job.status === 'timeout') return job
      await new Promise((r) => setTimeout(r, intervalMs))
    }
    throw new Error('poll_timeout')
  }

  return { items, loading, error, refresh, create, poll }
})
