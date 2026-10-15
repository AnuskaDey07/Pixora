import { createRouter, createWebHistory } from 'vue-router'
import { hasToken } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/gallery' },
    { path: '/login', name: 'login', component: () => import('@/views/Login.vue'), meta: { public: true } },
    { path: '/register', name: 'register', component: () => import('@/views/Register.vue'), meta: { public: true } },
    { path: '/gallery', name: 'gallery', component: () => import('@/views/Gallery.vue') },
    { path: '/upload', name: 'upload', component: () => import('@/views/Upload.vue') },
    { path: '/editor', name: 'editor', component: () => import('@/views/Editor.vue') },
    { path: '/search', name: 'search', component: () => import('@/views/Search.vue') },
    { path: '/profile', name: 'profile', component: () => import('@/views/Profile.vue') },
    {
      path: '/admin/nsfw',
      name: 'admin-nsfw',
      component: () => import('@/views/admin/NsfwQueue.vue'),
      meta: { requiresAdmin: true },
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFound.vue'), meta: { public: true } },
  ],
})

router.beforeEach((to) => {
  if (to.meta.public) return true
  if (!hasToken()) return { name: 'login', query: { redirect: to.fullPath } }

  if (to.meta.requiresAdmin) {
    const auth = useAuthStore()
    if (auth.user && !auth.isAdmin) return { name: 'gallery' }
  }
  return true
})

export default router
