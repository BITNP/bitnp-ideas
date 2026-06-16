import api from '@/api/client'
import type { IdeaRead, IdeaCreate, IdeaUpdate, IdeaStatusUpdate, ApiMessage } from '@/types/api'

export const ideasApi = {
  list() { return api.get<IdeaRead[]>('/ideas') },
  create(data: IdeaCreate) { return api.post<IdeaRead>('/ideas', data) },
  get(id: string) { return api.get<IdeaRead>(`/ideas/${id}`) },
  update(id: string, data: IdeaUpdate) { return api.patch<IdeaRead>(`/ideas/${id}`, data) },
  delete(id: string) { return api.delete<ApiMessage>(`/ideas/${id}`) },
  updateStatus(id: string, data: IdeaStatusUpdate) { return api.post<ApiMessage>(`/ideas/${id}/status`, data) },
  addTag(id: string, tagId: string) { return api.post<ApiMessage>(`/ideas/${id}/tags`, { tag_ids: [tagId] }) },
  removeTag(id: string, tagId: string) { return api.delete<ApiMessage>(`/ideas/${id}/tags/${tagId}`) },
}
