import api from '@/api/client'
import type { ExternalLinkRead, ExternalLinkCreate, LinkPreview, ApiMessage } from '@/types/api'

export const linksApi = {
  list(entityType: string, entityId: string) { return api.get<ExternalLinkRead[]>(`/${entityType}/${entityId}/links`) },
  create(entityType: string, entityId: string, data: ExternalLinkCreate) { return api.post<ExternalLinkRead>(`/${entityType}/${entityId}/links`, data) },
  delete(id: string) { return api.delete<ApiMessage>(`/links/${id}`) },
  preview(url: string) { return api.post<LinkPreview>('/links/preview', { url }) },
}
