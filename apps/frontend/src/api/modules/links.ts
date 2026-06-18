import api from '@/api/client'
import type {
  ExternalLinkRead,
  ExternalLinkCreate,
  ExternalLinkEntityType,
  LinkPreview,
  ApiMessage,
  PaginationParams,
  PageResponse,
} from '@/types/api'

export const linksApi = {
  list(entityType: ExternalLinkEntityType, entityId: string, params: PaginationParams = {}) {
    return api.get<PageResponse<ExternalLinkRead>>(`/${entityType}/${entityId}/links`, { params })
  },
  create(entityType: ExternalLinkEntityType, entityId: string, data: ExternalLinkCreate) { return api.post<ExternalLinkRead>(`/${entityType}/${entityId}/links`, data) },
  delete(id: string) { return api.delete<ApiMessage>(`/links/${id}`) },
  preview(url: string) { return api.post<LinkPreview>('/links/preview', { url }) },
}
