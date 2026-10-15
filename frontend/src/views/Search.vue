<script setup lang="ts">
import { ref } from 'vue'
import { semanticSearch, similarSearch, type SearchResult } from '@/api/search'

const query = ref('')
const results = ref<SearchResult[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const mode = ref<'semantic' | 'similar'>('semantic')

async function search() {
  if (!query.value.trim()) return
  loading.value = true
  error.value = null
  try {
    const res = await semanticSearch(query.value, 30)
    results.value = res.results
    mode.value = 'semantic'
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'search_failed'
  } finally {
    loading.value = false
  }
}

async function similar(imageId: string) {
  loading.value = true
  error.value = null
  try {
    const res = await similarSearch(imageId, 30)
    results.value = res.results
    mode.value = 'similar'
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'similar_failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-6xl px-6 py-8">
    <h1 class="text-2xl font-bold">Search</h1>
    <p class="mt-1 text-sm text-slate-400">Semantic search over your image library.</p>

    <form @submit.prevent="search" class="mt-6 flex gap-2">
      <input
        v-model="query"
        placeholder="e.g. sunset over mountains"
        class="flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
      />
      <button
        type="submit"
        :disabled="loading"
        class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
      >{{ loading ? 'Searching…' : 'Search' }}</button>
    </form>

    <div v-if="error" class="mt-4 rounded-md bg-rose-500/10 px-3 py-2 text-sm text-rose-300">{{ error }}</div>

    <div v-if="mode === 'similar'" class="mt-4 text-sm text-slate-400">Showing images similar to your selection.</div>

    <div v-if="results.length > 0" class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
      <div v-for="r in results" :key="r.image_id" class="overflow-hidden rounded-lg border border-slate-800 bg-slate-900">
        <div class="aspect-square overflow-hidden bg-slate-950">
          <img v-if="r.thumb_url" :src="r.thumb_url" class="h-full w-full object-cover" />
        </div>
        <div class="p-2">
          <div class="truncate text-xs text-slate-300">{{ r.filename ?? r.image_id.slice(0, 8) }}</div>
          <div class="text-[10px] text-slate-500">score {{ (r.score).toFixed(3) }}</div>
          <button
            @click="similar(r.image_id)"
            class="mt-2 w-full rounded border border-slate-700 py-1 text-xs text-slate-300 hover:border-brand-500"
          >Find similar</button>
        </div>
      </div>
    </div>

    <div v-else-if="!loading" class="mt-10 rounded-lg border border-dashed border-slate-800 p-10 text-center text-sm text-slate-500">
      Enter a query above, or click "Find similar" on any result.
    </div>
  </div>
</template>
