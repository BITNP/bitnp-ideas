import api from '@/api/client'
import type { TagRead, TagCreate, TagUpdate, ApiMessage, PageResponse, PaginationParams } from '@/types/api'

export const tagsApi = {
  list(params: PaginationParams = {}) { return api.get<PageResponse<TagRead>>('/idea-tags', { params }) },
  create(data: TagCreate) { return api.post<TagRead>('/idea-tags', data) },
  get(id: string) { return api.get<TagRead>(`/idea-tags/${id}`) },
  update(id: string, data: TagUpdate) { return api.patch<TagRead>(`/idea-tags/${id}`, data) },
  delete(id: string) { return api.delete<ApiMessage>(`/idea-tags/${id}`) },
}
