import api from '@/api/client'
import type {
  ExternalLinkRead,
  ExternalLinkCreate,
  LinkPreview,
  ApiMessage,
  PaginationParams,
  PageResponse,
} from '@/types/api'

export const linksApi = {
  list(entityType: string, entityId: string, params: PaginationParams = {}) {
    return api.get<PageResponse<ExternalLinkRead>>(`/${entityType}/${entityId}/links`, { params })
  },
  create(entityType: string, entityId: string, data: ExternalLinkCreate) { return api.post<ExternalLinkRead>(`/${entityType}/${entityId}/links`, data) },
  delete(id: string) { return api.delete<ApiMessage>(`/links/${id}`) },
  preview(url: string) { return api.post<LinkPreview>('/links/preview', { url }) },
}
