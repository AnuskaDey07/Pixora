<script setup lang="ts">
import { onMounted, ref } from 'vue'

const apiStatus = ref<'checking' | 'ok' | 'down'>('checking')
const apiPayload = ref<Record<string, unknown> | null>(null)

onMounted(async () => {
  try {
    const res = await fetch('/api/health')
    if (!res.ok) throw new Error(String(res.status))
    apiPayload.value = await res.json()
    apiStatus.value = 'ok'
  } catch {
    apiStatus.value = 'down'
  }
})
</script>

<template>
  <main class="min-h-full flex items-center justify-center p-8">
    <div class="max-w-lg w-full rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl">
      <h1 class="text-3xl font-bold tracking-tight">
        <span class="text-brand-400">Pixora</span>
      </h1>
      <p class="mt-2 text-slate-400 text-sm">
        Unified image platform — Batch 1: infrastructure is live.
      </p>

      <div class="mt-6 flex items-center gap-3 text-sm">
        <span
          class="inline-block h-2.5 w-2.5 rounded-full"
          :class="{
            'bg-amber-400 animate-pulse': apiStatus === 'checking',
            'bg-emerald-400': apiStatus === 'ok',
            'bg-rose-500': apiStatus === 'down',
          }"
        />
        <span v-if="apiStatus === 'checking'">Checking API…</span>
        <span v-else-if="apiStatus === 'ok'">API is online</span>
        <span v-else>API is unreachable</span>
      </div>

      <pre
        v-if="apiPayload"
        class="mt-4 rounded-lg bg-slate-950 p-3 text-xs text-slate-300 overflow-x-auto"
      >{{ JSON.stringify(apiPayload, null, 2) }}</pre>
    </div>
  </main>
</template>
