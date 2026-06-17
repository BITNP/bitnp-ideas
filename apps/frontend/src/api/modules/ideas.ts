import api from '@/api/client'
import type {
  IdeaRead,
  IdeaStatusHistoryRead,
  IdeaCreate,
  IdeaUpdate,
  IdeaStatusUpdate,
  ApiMessage,
  PaginationParams,
  PageResponse,
} from '@/types/api'

export interface IdeaListParams extends PaginationParams {
  status?: string
  tag?: string
  search?: string
}

export const ideasApi = {
  list(params: IdeaListParams = {}) { return api.get<PageResponse<IdeaRead>>('/ideas', { params }) },
  create(data: IdeaCreate) { return api.post<IdeaRead>('/ideas', data) },
  get(id: string) { return api.get<IdeaRead>(`/ideas/${id}`) },
  update(id: string, data: IdeaUpdate) { return api.patch<IdeaRead>(`/ideas/${id}`, data) },
  delete(id: string) { return api.delete<ApiMessage>(`/ideas/${id}`) },
  updateStatus(id: string, data: IdeaStatusUpdate) { return api.post<ApiMessage>(`/ideas/${id}/status`, data) },
  history(id: string, params: PaginationParams = {}) {
    return api.get<PageResponse<IdeaStatusHistoryRead>>(`/ideas/${id}/history`, { params })
  },
  addTag(id: string, tagId: string) { return api.post<ApiMessage>(`/ideas/${id}/tags`, { tag_ids: [tagId] }) },
  removeTag(id: string, tagId: string) { return api.delete<ApiMessage>(`/ideas/${id}/tags/${tagId}`) },
}
