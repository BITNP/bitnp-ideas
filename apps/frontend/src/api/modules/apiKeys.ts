import api from '@/api/client'
import type {
  ApiKeyRead,
  ApiKeyCreate,
  ApiKeyUpdate,
  ApiMessage,
  ApiKeyCreateResponse,
  PaginationParams,
  PageResponse,
} from '@/types/api'

export const apiKeysApi = {
  list(params: PaginationParams = {}) { return api.get<PageResponse<ApiKeyRead>>('/api-keys', { params }) },
  create(data: ApiKeyCreate) { return api.post<ApiKeyCreateResponse>('/api-keys', data) },
  update(id: string, data: ApiKeyUpdate) { return api.patch<ApiMessage>(`/api-keys/${id}`, data) },
  revoke(id: string) { return api.delete<ApiMessage>(`/api-keys/${id}`) },
  delete(id: string) { return api.delete<ApiMessage>(`/api-keys/${id}`) },
  rotate(id: string) { return api.post<ApiKeyCreateResponse>(`/api-keys/${id}/rotate`) },
}
