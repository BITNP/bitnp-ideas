import api from '@/api/client'
import type { ActivityRead } from '@/types/api'

export const activityApi = {
  list(projectId: string) { return api.get<ActivityRead[]>(`/projects/${projectId}/activity`) },
}
