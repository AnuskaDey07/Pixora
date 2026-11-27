import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useJobsStore } from './jobs'
import type { Job } from '@/api/jobs'

export type EditorTool =
  | 'resize' | 'convert' | 'remove_bg' | 'detect_nsfw' | 'detect_ai'
  | 'detect_objects' | 'generate' | 'img2img' | 'inpaint' | 'controlnet' | 'embed'

export const useEditorStore = defineStore('editor', () => {
  const imageId = ref<string | null>(null)
  const tool = ref<EditorTool>('resize')
  const params = ref<Record<string, unknown>>({})
  
  // We store state per tool so they don't overwrite each other
  const activeJobs = ref<Record<string, {
    job: Job | null
    resultUrl: string | null
    resultMeta: Record<string, unknown> | null
    error: string | null
    busy: boolean
  }>>({})

  function _initTool(t: EditorTool) {
    if (!activeJobs.value[t]) {
      activeJobs.value[t] = { job: null, resultUrl: null, resultMeta: null, error: null, busy: false }
    }
  }

  // Helper to get the current tool's state
  const currentState = computed(() => {
    _initTool(tool.value)
    return activeJobs.value[tool.value]
  })

  const isRunning = computed(() => Object.values(activeJobs.value).some(s => s.busy))
  const runningCount = computed(() => Object.values(activeJobs.value).filter(s => s.busy).length)

  function setImage(id: string | null) {
    imageId.value = id
    activeJobs.value = {} // Clear all results when changing image
  }

  function setTool(t: EditorTool) {
    tool.value = t
    _initTool(t)
    params.value = defaultsFor(t)
  }

  function cancel(t: EditorTool) {
    if (activeJobs.value[t]) {
      activeJobs.value[t].busy = false
      activeJobs.value[t].job = null
    }
  }

  function defaultsFor(t: EditorTool): Record<string, unknown> {
    switch (t) {
      case 'resize': return { width: 512, height: 512 }
      case 'convert': return { format: 'PNG' }
      case 'detect_objects': return { confidence_threshold: 0.15 }
      case 'generate': return { prompt: '', width: 512, height: 512 }
      default: return {}
    }
  }

  async function run() {
    if (!imageId.value && tool.value !== 'generate') return
    
    // Check concurrency limit
    if (runningCount.value >= 3) {
      currentState.value.error = 'Maximum 3 concurrent features. Wait or cancel one.'
      return
    }

    const t = tool.value
    _initTool(t)
    const state = activeJobs.value[t]
    
    state.busy = true
    state.error = null
    state.job = null
    state.resultUrl = null
    state.resultMeta = null

    try {
      const jobsStore = useJobsStore()
      const j = await jobsStore.create({
        type: t,
        image_id: imageId.value ?? undefined,
        params: params.value,
      })

      // If cancelled while starting
      if (!state.busy) return
      state.job = j

      const started = Date.now()
      const TIMEOUT_MS = 90_000

      while (Date.now() - started < TIMEOUT_MS) {
        if (!state.busy) return // Cancelled
        
        const current = await jobsStore.poll(j.id, 2000, 5_000)
        
        if (!state.busy) return
        state.job = current

        if (current.status === 'done') {
          state.resultUrl = current.result_url
          state.resultMeta = current.meta
          return
        }
        if (current.status === 'failed' || current.status === 'timeout') {
          state.error = current.error ?? current.status
          return
        }
      }
      state.error = 'timed_out_client_side'
    } catch (e: any) {
      state.error = e?.message ?? 'run_failed'
    } finally {
      state.busy = false
    }
  }

  return {
    imageId, tool, params, activeJobs,
    currentState, isRunning, runningCount,
    setImage, setTool, cancel, run
  }
})