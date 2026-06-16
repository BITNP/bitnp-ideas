import { createRouter, createWebHistory } from 'vue-router'

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
  { path: '/settings', name: 'settings', component: () => import('@/pages/SettingsPage.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

