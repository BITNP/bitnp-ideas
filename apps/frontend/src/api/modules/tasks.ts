import api from '@/api/client'
import type { TaskRead, TaskCreate, TaskUpdate, ApiMessage } from '@/types/api'

export const tasksApi = {
  list(projectId: string) { return api.get<TaskRead[]>(`/projects/${projectId}/tasks`) },
  create(projectId: string, data: TaskCreate) { return api.post<TaskRead>(`/projects/${projectId}/tasks`, data) },
  get(id: string) { return api.get<TaskRead>(`/tasks/${id}`) },
  update(id: string, data: TaskUpdate) { return api.patch<TaskRead>(`/tasks/${id}`, data) },
  delete(id: string) { return api.delete<ApiMessage>(`/tasks/${id}`) },
}
