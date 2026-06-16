import api from '@/api/client'
import type { ApiMessage, CurrentUser } from '@/types/api'

export const usersApi = {
  list() { return api.get<CurrentUser[]>('/users') },
  get(id: string) { return api.get<CurrentUser>(`/users/${id}`) },
  updateRole(id: string, globalRole: string) { return api.patch<ApiMessage>(`/users/${id}/role`, null, { params: { role: globalRole } }) },
  updateActive(id: string, isActive: boolean) { return api.patch<ApiMessage>(`/users/${id}/active`, null, { params: { is_active: isActive } }) },
}
