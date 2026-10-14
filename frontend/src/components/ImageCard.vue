<script setup lang="ts">
import type { ImageRecord } from '@/api/images'

defineProps<{ image: ImageRecord }>()
defineEmits<{ (e: 'delete', id: string): void }>()
</script>

<template>
  <div class="group relative overflow-hidden rounded-lg border border-slate-800 bg-slate-900">
    <div class="aspect-square overflow-hidden bg-slate-950">
      <img
        v-if="image.thumb_url"
        :src="image.thumb_url"
        :alt="image.filename ?? 'image'"
        class="h-full w-full object-cover transition group-hover:scale-105"
        loading="lazy"
      />
      <div v-else class="flex h-full items-center justify-center text-slate-600">no thumb</div>
    </div>

    <div class="p-3">
      <div class="truncate text-sm text-slate-300">{{ image.filename ?? 'untitled' }}</div>
      <div class="mt-1 text-xs text-slate-500">
        {{ image.width }}×{{ image.height }} · {{ (image.size_bytes / 1024).toFixed(0) }} KB
      </div>
    </div>

    <button
      @click="$emit('delete', image.id)"
      class="absolute right-2 top-2 hidden rounded-md bg-rose-600/90 px-2 py-1 text-xs text-white hover:bg-rose-500 group-hover:block"
    >Delete</button>
  </div>
</template>
