<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useImagesStore } from '@/stores/images'

const images = useImagesStore()
const router = useRouter()

const file = ref<File | null>(null)
const previewUrl = ref<string | null>(null)
const uploading = ref(false)
const dragging = ref(false)
const localError = ref<string | null>(null)

function revokePreview() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = null
  }
}

function acceptFile(f: File) {
  file.value = f
  revokePreview()
  previewUrl.value = URL.createObjectURL(f)
  localError.value = null
}

function onSelect(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) acceptFile(f)
}

function onDragEnter(e: DragEvent) {
  e.preventDefault()
  dragging.value = true
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy'
}

function onDragLeave(e: DragEvent) {
  e.preventDefault()
  // only exit when leaving the zone, not a child element
  if (e.target === e.currentTarget) dragging.value = false
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  dragging.value = false
  const f = e.dataTransfer?.files?.[0]
  if (!f) return
  if (!f.type.startsWith('image/')) {
    localError.value = 'only_image_files'
    return
  }
  acceptFile(f)
}

async function submit() {
  if (!file.value) return
  uploading.value = true
  localError.value = null
  try {
    await images.upload(file.value)
    router.push('/gallery')
  } catch {
    localError.value = images.error ?? 'upload_failed'
  } finally {
    uploading.value = false
  }
}

onBeforeUnmount(revokePreview)
</script>

<template>
  <div class="mx-auto max-w-2xl px-6 py-8">
    <h1 class="text-2xl font-bold">Upload an image</h1>
    <p class="mt-1 text-sm text-slate-400">PNG, JPEG, or WebP. Max 50 MB.</p>

    <form @submit.prevent="submit" class="mt-6 space-y-4">
      <label
        @dragenter="onDragEnter"
        @dragover="onDragOver"
        @dragleave="onDragLeave"
        @drop="onDrop"
        class="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-12 transition"
        :class="{
          'border-brand-500 bg-brand-500/10': dragging,
          'border-slate-700 bg-slate-900/40 hover:border-brand-500': !dragging,
        }"
      >
        <input
          type="file"
          accept="image/png,image/jpeg,image/webp"
          class="hidden"
          @change="onSelect"
        />
        <div v-if="!previewUrl" class="text-center">
          <p class="text-slate-300">Click to choose a file</p>
          <p class="mt-1 text-xs text-slate-500">or drag and drop it here</p>
        </div>
        <img v-else :src="previewUrl" alt="preview" class="max-h-64 rounded-md object-contain" />
      </label>

      <div v-if="file" class="text-sm text-slate-400">
        {{ file.name }} — {{ (file.size / 1024).toFixed(0) }} KB
      </div>

      <div v-if="localError" class="rounded-md bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
        {{ localError }}
      </div>

      <div class="flex gap-3">
        <button
          type="submit"
          :disabled="!file || uploading"
          class="rounded-md bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-500 disabled:opacity-50"
        >{{ uploading ? 'Uploading…' : 'Upload' }}</button>
        <RouterLink
          to="/gallery"
          class="rounded-md border border-slate-700 px-4 py-2 text-slate-300 hover:border-slate-500"
        >Cancel</RouterLink>
      </div>
    </form>
  </div>
</template>
