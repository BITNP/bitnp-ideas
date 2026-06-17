import api from '@/api/client'
import type { ActivityRead, PageResponse, PaginationParams } from '@/types/api'

export interface ActivityListParams extends PaginationParams {
  actor_user_id?: string
  action_type?: string
  entity_type?: string
}

export const activityApi = {
  list(projectId: string, params: ActivityListParams = {}) {
    return api.get<PageResponse<ActivityRead>>(`/projects/${projectId}/activity`, { params })
  },
}
