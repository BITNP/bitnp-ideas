import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', name: 'login', component: () => import('@/pages/LoginPage.vue') },
  { path: '/dashboard', name: 'dashboard', component: () => import('@/pages/DashboardPage.vue') },
  { path: '/ideas', name: 'ideas', component: () => import('@/pages/IdeasPage.vue') },
  { path: '/ideas/:id', name: 'idea-detail', component: () => import('@/pages/IdeasPage.vue') },
  { path: '/projects', name: 'projects', component: () => import('@/pages/ProjectsPage.vue') },
  { path: '/projects/:id', name: 'project-detail', component: () => import('@/pages/ProjectDetailPage.vue') },
  { path: '/projects/:id/tasks', name: 'project-tasks', component: () => import('@/pages/ProjectDetailPage.vue') },
  { path: '/projects/:id/gantt', name: 'project-gantt', component: () => import('@/pages/ProjectDetailPage.vue') },
  { path: '/projects/:id/activity', name: 'project-activity', component: () => import('@/pages/ProjectDetailPage.vue') },
  { path: '/api-keys', name: 'api-keys', component: () => import('@/pages/ApiKeysPage.vue') },
  { path: '/users', name: 'users', component: () => import('@/pages/UsersPage.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ── Auth guard ───────────────────────────────────────────
const PUBLIC_ROUTES = ['/login']
let sessionRestored = false

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()

  // Restore session once on first navigation
  if (!sessionRestored) {
    sessionRestored = true
    await auth.restoreSession()
  }

  // Public route — allow, but redirect to dashboard if already authenticated
  if (PUBLIC_ROUTES.includes(to.path)) {
    if (auth.isAuthenticated) {
      return next('/dashboard')
    }
    return next()
  }

  // Protected route — require authentication
  if (!auth.isAuthenticated) {
    return next('/login')
  }

  next()
})

export default router
