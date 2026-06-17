import api from '@/api/client'
import type {
  ProjectRead,
  ProjectCreate,
  ProjectUpdate,
  IdeaRead,
  ApiMessage,
  PaginationParams,
  PageResponse,
} from '@/types/api'

export const projectsApi = {
  list(params: PaginationParams = {}) { return api.get<PageResponse<ProjectRead>>('/projects', { params }) },
  create(data: ProjectCreate) { return api.post<ProjectRead>('/projects', data) },
  get(id: string) { return api.get<ProjectRead>(`/projects/${id}`) },
  update(id: string, data: ProjectUpdate) { return api.patch<ProjectRead>(`/projects/${id}`, data) },
  delete(id: string) { return api.delete<ApiMessage>(`/projects/${id}`) },
  addMember(projectId: string, userId: string) { return api.post<ApiMessage>(`/projects/${projectId}/members`, { user_id: userId }) },
  removeMember(projectId: string, userId: string) { return api.delete<ApiMessage>(`/projects/${projectId}/members/${userId}`) },
  listIdeas(projectId: string, params: PaginationParams = {}) { return api.get<PageResponse<IdeaRead>>(`/projects/${projectId}/ideas`, { params }) },
  addIdea(projectId: string, ideaId: string, relationType = 'related') {
    return api.post<ApiMessage>(`/projects/${projectId}/ideas`, {
      idea_id: ideaId,
      relation_type: relationType,
    })
  },
  removeIdea(projectId: string, ideaId: string) { return api.delete<ApiMessage>(`/projects/${projectId}/ideas/${ideaId}`) },
}
