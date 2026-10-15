import { ref, onUnmounted } from 'vue'
import { getJob, type Job } from '@/api/jobs'

export function useJob(jobId: string, intervalMs = 2000) {
  const job = ref<Job | null>(null)
  const error = ref<string | null>(null)
  let timer: number | null = null
  let stopped = false

  async function tick() {
    if (stopped) return
    try {
      const j = await getJob(jobId)
      job.value = j
      if (j.status === 'done' || j.status === 'failed' || j.status === 'timeout') {
        stop()
        return
      }
    } catch (e: any) {
      error.value = e?.response?.data?.error ?? 'poll_failed'
      stop()
      return
    }
    timer = window.setTimeout(tick, intervalMs)
  }

  function stop() {
    stopped = true
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
  }

  tick()
  onUnmounted(stop)

  return { job, error, stop }
}
