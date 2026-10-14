import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import type { User } from '@/api/auth'
import { hasToken, clearTokens } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!user.value && hasToken())
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function bootstrap() {
    if (!hasToken()) return
    try {
      user.value = await authApi.me()
    } catch {
      clearTokens()
      user.value = null
    }
  }

  async function login(email: string, password: string) {
    loading.value = true
    error.value = null
    try {
      user.value = await authApi.login(email, password)
    } catch (e: any) {
      error.value = e?.response?.data?.error ?? 'login_failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function register(email: string, password: string) {
    loading.value = true
    error.value = null
    try {
      await authApi.register(email, password)
      await login(email, password)
    } catch (e: any) {
      error.value = e?.response?.data?.error ?? 'register_failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  function logout() {
    authApi.logout()
    user.value = null
  }

  return { user, loading, error, isAuthenticated, isAdmin, bootstrap, login, register, logout }
})
