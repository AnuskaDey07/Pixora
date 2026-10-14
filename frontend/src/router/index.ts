import { createRouter, createWebHistory } from 'vue-router'
import { hasToken } from '@/api/client'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/gallery' },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/Register.vue'),
      meta: { public: true },
    },
    {
      path: '/gallery',
      name: 'gallery',
      component: () => import('@/views/Gallery.vue'),
    },
    {
      path: '/upload',
      name: 'upload',
      component: () => import('@/views/Upload.vue'),
    },
  ],
})

router.beforeEach((to) => {
  if (to.meta.public) return true
  if (!hasToken()) return { name: 'login', query: { redirect: to.fullPath } }
  return true
})

export default router
