import api from '@/api/client'
import type { LoginResponse, CallbackResponse, CurrentUser, ApiMessage } from '@/types/api'

export const authApi = {
  login(redirectUri: string) {
    return api.get<LoginResponse>('/auth/login', { params: { redirect_uri: redirectUri } })
  },
  callback(code: string, state: string, redirectUri: string) {
    return api.get<CallbackResponse>('/auth/callback', { params: { code, state, redirect_uri: redirectUri } })
  },
  me() {
    return api.get<CurrentUser>('/auth/me')
  },
  logout() {
    return api.post<ApiMessage>('/auth/logout')
  },
}
