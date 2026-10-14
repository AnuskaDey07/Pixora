import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as imagesApi from '@/api/images'
import type { ImageRecord } from '@/api/images'

export const useImagesStore = defineStore('images', () => {
  const items = ref<ImageRecord[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function refresh(limit = 40, offset = 0) {
    loading.value = true
    error.value = null
    try {
      const res = await imagesApi.listImages(limit, offset)
      items.value = res.images
    } catch (e: any) {
      error.value = e?.response?.data?.error ?? 'load_failed'
    } finally {
      loading.value = false
    }
  }

  async function upload(file: File) {
    loading.value = true
    error.value = null
    try {
      const record = await imagesApi.uploadImage(file)
      items.value = [record, ...items.value]
      return record
    } catch (e: any) {
      error.value = e?.response?.data?.error ?? 'upload_failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function remove(id: string) {
    await imagesApi.deleteImage(id)
    items.value = items.value.filter((i) => i.id !== id)
  }

  return { items, loading, error, refresh, upload, remove }
})
