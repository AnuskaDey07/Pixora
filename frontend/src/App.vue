<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import Nav from '@/components/Nav.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()

onMounted(() => {
  auth.bootstrap()

  // Prevent the browser from opening dropped files when the user
  // misses the drop zone.
  const stop = (e: DragEvent) => { e.preventDefault() }
  window.addEventListener('dragover', stop)
  window.addEventListener('drop', stop)
})
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100">
    <Nav v-if="!route.meta.public" />
    <RouterView />
  </div>
</template>
