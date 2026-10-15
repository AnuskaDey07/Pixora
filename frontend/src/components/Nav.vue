<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <nav class="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
    <div class="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
      <RouterLink to="/gallery" class="flex items-center gap-2">
        <span class="text-xl font-bold text-brand-400">Pixora</span>
      </RouterLink>

      <div v-if="auth.isAuthenticated" class="flex items-center gap-5 text-sm">
        <RouterLink to="/gallery" class="text-slate-300 hover:text-white">Gallery</RouterLink>
        <RouterLink to="/upload" class="text-slate-300 hover:text-white">Upload</RouterLink>
        <RouterLink to="/editor" class="text-slate-300 hover:text-white">Editor</RouterLink>
        <RouterLink to="/search" class="text-slate-300 hover:text-white">Search</RouterLink>
        <RouterLink
          v-if="auth.isAdmin"
          to="/admin/nsfw"
          class="text-amber-300 hover:text-amber-200"
        >NSFW Queue</RouterLink>

        <RouterLink
          to="/profile"
          class="text-slate-400 hover:text-white"
          :title="auth.user?.email ?? ''"
        >{{ auth.user?.email?.split('@')[0] ?? 'profile' }}</RouterLink>

        <button
          @click="handleLogout"
          class="rounded-md border border-slate-700 px-3 py-1.5 text-slate-300 hover:border-slate-500 hover:text-white"
        >Log out</button>
      </div>
    </div>
  </nav>
</template>
