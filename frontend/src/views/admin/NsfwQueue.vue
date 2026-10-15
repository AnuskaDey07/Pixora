<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { nsfwQueue, approveNsfw, rejectNsfw, type NsfwQueueItem } from '@/api/admin'

const items = ref<NsfwQueueItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

async function refresh() {
  loading.value = true
  error.value = null
  try {
    const res = await nsfwQueue()
    items.value = res.images
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'load_failed'
  } finally {
    loading.value = false
  }
}

async function approve(id: string) {
  await approveNsfw(id)
  items.value = items.value.filter((i) => i.id !== id)
}

async function reject(id: string) {
  if (!confirm('Reject and permanently delete this image?')) return
  await rejectNsfw(id)
  items.value = items.value.filter((i) => i.id !== id)
}

onMounted(refresh)
</script>

<template>
  <div class="mx-auto max-w-6xl px-6 py-8">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">NSFW review queue</h1>
        <p class="mt-1 text-sm text-slate-400">Images flagged by automated detection. Approve or reject.</p>
      </div>
      <button
        @click="refresh"
        class="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:border-slate-500"
      >Refresh</button>
    </div>

    <div v-if="error" class="mt-4 rounded-md bg-rose-500/10 px-3 py-2 text-sm text-rose-300">{{ error }}</div>

    <div v-if="loading" class="mt-8 text-slate-500">Loading…</div>

    <div v-else-if="items.length === 0" class="mt-10 rounded-lg border border-dashed border-slate-800 p-10 text-center text-sm text-slate-500">
      Nothing flagged. Queue is clean.
    </div>

    <div v-else class="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
      <div v-for="item in items" :key="item.id" class="overflow-hidden rounded-lg border border-slate-800 bg-slate-900">
        <div class="aspect-square overflow-hidden bg-slate-950">
          <img v-if="item.thumb_url" :src="item.thumb_url" class="h-full w-full object-cover" />
          <div v-else class="flex h-full items-center justify-center text-xs text-slate-600">no thumb</div>
        </div>
        <div class="space-y-2 p-3">
          <div class="text-xs text-slate-400">score: {{ item.nsfw_score?.toFixed(3) ?? '—' }}</div>
          <div class="truncate text-xs text-slate-500">user: {{ item.user_id.slice(0, 8) }}</div>
          <div class="flex gap-2">
            <button
              @click="approve(item.id)"
              class="flex-1 rounded-md bg-emerald-600/20 px-3 py-1.5 text-xs text-emerald-300 hover:bg-emerald-600/30"
            >Approve</button>
            <button
              @click="reject(item.id)"
              class="flex-1 rounded-md bg-rose-600/20 px-3 py-1.5 text-xs text-rose-300 hover:bg-rose-600/30"
            >Reject</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
