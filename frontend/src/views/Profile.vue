<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api/client'

const auth = useAuthStore()

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const saving = ref(false)
const message = ref<string | null>(null)
const error = ref<string | null>(null)

async function changePassword() {
  message.value = null
  error.value = null

  if (newPassword.value !== confirmPassword.value) {
    error.value = 'passwords_do_not_match'
    return
  }
  if (newPassword.value.length < 8) {
    error.value = 'password_too_short'
    return
  }
  if (oldPassword.value === newPassword.value) {
    error.value = 'same_password'
    return
  }

  saving.value = true
  try {
    await api.post('/auth/change-password', {
      old_password: oldPassword.value,
      new_password: newPassword.value,
    })
    message.value = 'password_changed'
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (e: any) {
    error.value = e?.response?.data?.error ?? 'change_failed'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-2xl px-6 py-8">
    <h1 class="text-2xl font-bold">Profile</h1>
    <p class="mt-1 text-sm text-slate-400">Account details and security.</p>

    <!-- Account info -->
    <section class="mt-6 rounded-lg border border-slate-800 bg-slate-900/50 p-6">
      <h2 class="text-sm uppercase tracking-wide text-slate-500">Account</h2>
      <dl class="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt class="text-slate-500">Email</dt>
          <dd class="mt-0.5 text-slate-200">{{ auth.user?.email }}</dd>
        </div>
        <div>
          <dt class="text-slate-500">Role</dt>
          <dd class="mt-0.5">
            <span
              class="rounded-full px-2 py-0.5 text-xs"
              :class="auth.isAdmin
                ? 'bg-amber-500/20 text-amber-300'
                : 'bg-slate-700/50 text-slate-300'"
            >{{ auth.user?.role }}</span>
          </dd>
        </div>
        <div>
          <dt class="text-slate-500">User ID</dt>
          <dd class="mt-0.5 font-mono text-xs text-slate-400">{{ auth.user?.id }}</dd>
        </div>
        <div v-if="auth.user?.created_at">
          <dt class="text-slate-500">Member since</dt>
          <dd class="mt-0.5 text-slate-200">{{ new Date(auth.user.created_at).toLocaleDateString() }}</dd>
        </div>
      </dl>
    </section>

    <!-- Change password -->
    <section class="mt-6 rounded-lg border border-slate-800 bg-slate-900/50 p-6">
      <h2 class="text-sm uppercase tracking-wide text-slate-500">Change password</h2>

      <form @submit.prevent="changePassword" class="mt-4 space-y-3">
        <div>
          <label class="block text-xs text-slate-400">Current password</label>
          <input
            v-model="oldPassword"
            type="password"
            required
            autocomplete="current-password"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label class="block text-xs text-slate-400">New password</label>
          <input
            v-model="newPassword"
            type="password"
            required
            minlength="8"
            autocomplete="new-password"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label class="block text-xs text-slate-400">Confirm new password</label>
          <input
            v-model="confirmPassword"
            type="password"
            required
            minlength="8"
            autocomplete="new-password"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
        </div>

        <div v-if="message === 'password_changed'" class="rounded-md bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300">
          Password changed successfully.
        </div>
        <div v-if="error" class="rounded-md bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
          {{ error }}
        </div>

        <button
          type="submit"
          :disabled="saving"
          class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
        >{{ saving ? 'Saving…' : 'Change password' }}</button>
      </form>
    </section>
  </div>
</template>
