import api from '@/api/client'
import type { GanttRead, GanttBulkUpdate, TaskDependencyCreate, ApiMessage } from '@/types/api'

export const ganttApi = {
  get(projectId: string) { return api.get<GanttRead>(`/projects/${projectId}/gantt`) },
  bulkUpdate(projectId: string, data: GanttBulkUpdate) { return api.patch<ApiMessage>(`/projects/${projectId}/gantt/bulk`, data) },
  addDependency(projectId: string, data: TaskDependencyCreate) { return api.post<ApiMessage>(`/projects/${projectId}/task-dependencies`, data) },
  removeDependency(projectId: string, dependencyId: string) { return api.delete<ApiMessage>(`/projects/${projectId}/task-dependencies/${dependencyId}`) },
}
