import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
    meta: { public: true },
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
    meta: { roles: ['regular'] },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { roles: ['regular'] },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { roles: ['therapist', 'guardian'] },
  },
  { path: '/:catchAll(.*)', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    if (auth.isAuthenticated) {
      const home = auth.isRegular ? '/chat' : '/dashboard'
      return next({ path: home })
    }
    return next()
  }

  if (!auth.isAuthenticated) {
    return next({ path: '/login' })
  }

  const roles = to.meta.roles as string[] | undefined
  if (roles && !roles.includes(auth.user?.role ?? '')) {
    if (auth.isRegular) return next('/chat')
    return next('/dashboard')
  }

  return next()
})

export default router
