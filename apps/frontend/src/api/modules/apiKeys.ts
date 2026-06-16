import api from '@/api/client'
import type { ApiKeyRead, ApiKeyCreate, ApiKeyUpdate, ApiMessage } from '@/types/api'

export const apiKeysApi = {
  list() { return api.get<ApiKeyRead[]>('/api-keys') },
  create(data: ApiKeyCreate) { return api.post<ApiKeyRead>('/api-keys', data) },
  update(id: string, data: ApiKeyUpdate) { return api.patch<ApiKeyRead>(`/api-keys/${id}`, data) },
  delete(id: string) { return api.delete<ApiMessage>(`/api-keys/${id}`) },
  rotate(id: string) { return api.post<ApiKeyRead>(`/api-keys/${id}/rotate`) },
}
