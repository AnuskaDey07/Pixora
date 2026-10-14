<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const email = ref('')
const password = ref('')
const localError = ref<string | null>(null)

const auth = useAuthStore()
const router = useRouter()

async function submit() {
  localError.value = null
  try {
    await auth.register(email.value, password.value)
    router.push('/gallery')
  } catch {
    localError.value = auth.error ?? 'register_failed'
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center p-6">
    <div class="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/60 p-8">
      <h1 class="text-2xl font-bold">
        <span class="text-brand-400">Pixora</span>
      </h1>
      <p class="mt-1 text-sm text-slate-400">Create your account</p>

      <form @submit.prevent="submit" class="mt-6 space-y-4">
        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400">Email</label>
          <input
            v-model="email"
            type="email"
            required
            autocomplete="email"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-brand-500"
          />
        </div>

        <div>
          <label class="block text-xs uppercase tracking-wide text-slate-400">Password</label>
          <input
            v-model="password"
            type="password"
            required
            minlength="8"
            autocomplete="new-password"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-brand-500"
          />
          <p class="mt-1 text-xs text-slate-500">At least 8 characters</p>
        </div>

        <div v-if="localError" class="rounded-md bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
          {{ localError }}
        </div>

        <button
          type="submit"
          :disabled="auth.loading"
          class="w-full rounded-md bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-500 disabled:opacity-50"
        >{{ auth.loading ? 'Creating…' : 'Create account' }}</button>
      </form>

      <p class="mt-4 text-center text-sm text-slate-500">
        Already have an account?
        <RouterLink to="/login" class="text-brand-400 hover:underline">Sign in</RouterLink>
      </p>
    </div>
  </div>
</template>
