<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="flex min-h-[60vh] items-center justify-center p-6">
    <div class="max-w-md text-center">
      <p class="text-6xl font-bold text-slate-700">404</p>
      <h1 class="mt-4 text-xl font-semibold text-slate-200">Page not found</h1>
      <p class="mt-2 text-sm text-slate-400">
        The page you're looking for doesn't exist or has moved.
      </p>
      <div class="mt-6 flex justify-center gap-3">
        <button
          @click="router.back()"
          class="rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:border-slate-500"
        >Go back</button>
        <RouterLink
          to="/gallery"
          class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500"
        >Go to gallery</RouterLink>
      </div>
    </div>
  </div>
</template>
