import { defineStore } from 'pinia'
import { isAxiosError } from 'axios'
import type { CurrentUser, LoginResponse, CallbackResponse } from '@/types/api'
import api from '@/api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token'),
    user: JSON.parse(localStorage.getItem('user') || 'null') as CurrentUser | null,
    ready: false,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) =>
      state.user?.global_role === 'superuser' ||
      state.user?.global_role === 'administrator',
    isSuperuser: (state) => state.user?.global_role === 'superuser',
  },
  actions: {
    async login() {
      const redirectUri = window.location.origin + '/login'
      const response = await api.get<LoginResponse>('/auth/login', {
        params: { redirect_uri: redirectUri },
      })
      const { authorization_url, state: authState } = response.data
      localStorage.setItem('auth_state', authState)
      window.location.href = authorization_url
    },
    async handleCallback(code: string, state: string) {
      const redirectUri = window.location.origin + '/login'
      const expectedState = localStorage.getItem('auth_state')
      if (!expectedState || expectedState !== state) {
        localStorage.removeItem('auth_state')
        throw new Error('Invalid login state')
      }
      const response = await api.get<CallbackResponse>('/auth/callback', {
        params: { code, state, redirect_uri: redirectUri },
      })
      const { access_token, user } = response.data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('user', JSON.stringify(user))
      localStorage.removeItem('auth_state')
      this.token = access_token
      this.user = user
      return user
    },
    async restoreSession() {
      if (!this.token) {
        this.ready = true
        return
      }
      try {
        const response = await api.get<CurrentUser>('/auth/me')
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
      } catch (error) {
        // Token invalid → clear state without redirecting (router guard handles that)
        if (isAxiosError(error) && error.response?.status === 401) {
          this.token = null
          this.user = null
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
          localStorage.removeItem('auth_state')
        }
      } finally {
        this.ready = true
      }
    },
    async logout() {
      try {
        await api.post('/auth/logout')
      } catch {
        // best-effort
      }
      this.token = null
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      localStorage.removeItem('auth_state')
      window.location.href = '/login'
    },
  },
})
