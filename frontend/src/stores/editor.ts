import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as jobsApi from '@/api/jobs'
import type { Job } from '@/api/jobs'
import { useJobsStore } from './jobs'

export type EditorTool =
  | 'resize'
  | 'convert'
  | 'remove_bg'
  | 'detect_nsfw'
  | 'detect_ai'
  | 'detect_objects'
  | 'generate'
  | 'img2img'
  | 'inpaint'
  | 'controlnet'
  | 'embed'

export interface EditorSession {
  imageId: string | null
  tool: EditorTool
  params: Record<string, unknown>
  job: Job | null
  resultUrl: string | null
  resultMeta: Record<string, unknown> | null
  error: string | null
}

export const useEditorStore = defineStore('editor', () => {
  const imageId = ref<string | null>(null)
  const tool = ref<EditorTool>('resize')
  const params = ref<Record<string, unknown>>({ width: 512, height: 512 })
  const job = ref<Job | null>(null)
  const resultUrl = ref<string | null>(null)
  const resultMeta = ref<Record<string, unknown> | null>(null)
  const error = ref<string | null>(null)
  const busy = ref(false)

  const isRunning = computed(() =>
    job.value?.status === 'pending' || job.value?.status === 'running',
  )

  function reset() {
    job.value = null
    resultUrl.value = null
    resultMeta.value = null
    error.value = null
  }

  function setImage(id: string | null) {
    imageId.value = id
    reset()
  }

  function setTool(t: EditorTool) {
    tool.value = t
    reset()
    // sensible defaults per tool
    params.value = defaultsFor(t)
  }

  function defaultsFor(t: EditorTool): Record<string, unknown> {
    switch (t) {
      case 'resize':         return { width: 512, height: 512 }
      case 'convert':        return { format: 'PNG' }
      case 'generate':       return { prompt: '', width: 512, height: 512, steps: 20 }
      case 'img2img':        return { prompt: '', strength: 0.75, steps: 20 }
      case 'inpaint':        return { prompt: '', steps: 30, guidance: 7.5 }
      case 'controlnet':     return { prompt: '', control_strength: 1.0 }
      default:               return {}
    }
  }

  async function run() {
    if (!imageId.value && !['generate'].includes(tool.value)) {
      error.value = 'no_image_selected'
      return
    }
    busy.value = true
    error.value = null
    reset()

    try {
      const jobsStore = useJobsStore()
      const j = await jobsStore.create({
        type: tool.value,
        image_id: imageId.value ?? undefined,
        params: params.value,
      })
      job.value = j

      // Poll in the background
      const finished = await jobsStore.poll(j.id)
      job.value = finished

      if (finished.status === 'done') {
        resultUrl.value = finished.result_url
        resultMeta.value = finished.meta
      } else {
        error.value = finished.error ?? finished.status
      }
    } catch (e: any) {
      error.value = e?.message ?? 'run_failed'
    } finally {
      busy.value = false
    }
  }

  return {
    imageId, tool, params, job, resultUrl, resultMeta, error, busy,
    isRunning, reset, setImage, setTool, run,
  }
})
