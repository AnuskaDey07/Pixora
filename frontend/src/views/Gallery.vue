<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useImagesStore } from '@/stores/images'
import { useJobsStore } from '@/stores/jobs'
import { similarSearch } from '@/api/search'
import ImageCard from '@/components/ImageCard.vue'

const images = useImagesStore()
const jobs = useJobsStore()
const router = useRouter()

onMounted(async () => {
  await Promise.all([images.refresh(), jobs.refresh({ limit: 10 })])
})

async function handleDelete(id: string) {
  if (!confirm('Delete this image?')) return
  await images.remove(id)
}

async function resize(id: string, width: number, height: number) {
  const job = await jobs.create({ type: 'resize', image_id: id, params: { width, height } })
  await jobs.poll(job.id)
  await images.refresh()
}

async function findSimilar(id: string) {
  try {
    await similarSearch(id, 1)
    router.push({ name: 'search' })
  } catch {
    // ignore; search page will show results when user clicks
    router.push({ name: 'search' })
  }
}
</script>

<template>
  <div class="mx-auto max-w-6xl px-6 py-8">
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">Your gallery</h1>
        <p class="text-sm text-slate-400">{{ images.items.length }} images</p>
      </div>
      <RouterLink to="/upload" class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500">
        Upload image
      </RouterLink>
    </div>

    <div v-if="images.loading && images.items.length === 0" class="text-slate-500">Loading…</div>

    <div v-else-if="images.items.length === 0" class="rounded-lg border border-dashed border-slate-800 p-12 text-center">
      <p class="text-slate-400">No images yet.</p>
      <RouterLink to="/upload" class="mt-2 inline-block text-brand-400 hover:underline">Upload your first image →</RouterLink>
    </div>

    <div v-else class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
      <div v-for="img in images.items" :key="img.id" class="space-y-2">
        <ImageCard :image="img" @delete="handleDelete" />
        <div class="flex gap-2">
          <RouterLink
            :to="{ name: 'editor', query: { image: img.id } }"
            class="flex-1 rounded-md border border-slate-700 px-2 py-1.5 text-center text-xs text-slate-300 hover:border-brand-500 hover:text-white"
          >Edit</RouterLink>
          <button
            @click="findSimilar(img.id)"
            class="flex-1 rounded-md border border-slate-700 px-2 py-1.5 text-xs text-slate-300 hover:border-brand-500 hover:text-white"
          >Similar</button>
        </div>
        <button
          @click="resize(img.id, 256, 256)"
          class="w-full rounded-md border border-slate-700 px-3 py-1 text-xs text-slate-400 hover:border-brand-500 hover:text-white"
        >Resize 256×256</button>
      </div>
    </div>

    <div v-if="jobs.items.length > 0" class="mt-10">
      <h2 class="mb-3 text-sm uppercase tracking-wide text-slate-500">Recent jobs</h2>
      <div class="space-y-2">
        <div
          v-for="job in jobs.items.slice(0, 8)"
          :key="job.id"
          class="flex items-center justify-between rounded-md border border-slate-800 bg-slate-900/50 px-4 py-2 text-sm"
        >
          <div class="flex items-center gap-3">
            <span class="font-mono text-xs text-slate-400">{{ job.type }}</span>
            <span
              class="rounded-full px-2 py-0.5 text-xs"
              :class="{
                'bg-amber-500/20 text-amber-300': job.status === 'pending' || job.status === 'running',
                'bg-emerald-500/20 text-emerald-300': job.status === 'done',
                'bg-rose-500/20 text-rose-300': job.status === 'failed' || job.status === 'timeout',
              }"
            >{{ job.status }}</span>
          </div>
          <a v-if="job.result_url" :href="job.result_url" target="_blank" class="text-xs text-brand-400 hover:underline">open result</a>
        </div>
      </div>
    </div>
  </div>
</template>
