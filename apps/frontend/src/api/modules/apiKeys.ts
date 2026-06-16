import api from '@/api/client'
import type { ApiKeyRead, ApiKeyCreate, ApiKeyUpdate, ApiMessage, ApiKeyCreateResponse } from '@/types/api'

export const apiKeysApi = {
  list() { return api.get<ApiKeyRead[]>('/api-keys') },
  create(data: ApiKeyCreate) { return api.post<ApiKeyCreateResponse>('/api-keys', data) },
  update(id: string, data: ApiKeyUpdate) { return api.patch<ApiMessage>(`/api-keys/${id}`, data) },
  delete(id: string) { return api.delete<ApiMessage>(`/api-keys/${id}`) },
  rotate(id: string) { return api.post<ApiKeyCreateResponse>(`/api-keys/${id}/rotate`) },
}
