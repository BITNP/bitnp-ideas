import api from '@/api/client'
import type { CurrentUser, ApiMessage } from '@/types/api'

export const usersApi = {
  list() { return api.get<CurrentUser[]>('/users') },
  get(id: string) { return api.get<CurrentUser>(`/users/${id}`) },
  updateRole(id: string, globalRole: string) { return api.patch<CurrentUser>(`/users/${id}/role`, { global_role: globalRole }) },
  updateActive(id: string, isActive: boolean) { return api.patch<CurrentUser>(`/users/${id}/active`, { is_active: isActive }) },
}
