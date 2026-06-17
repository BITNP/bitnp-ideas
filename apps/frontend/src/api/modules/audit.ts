import api from '@/api/client'
import type { AuditLogRead, PageResponse, PaginationParams } from '@/types/api'

export interface AuditLogFilters extends PaginationParams {
  actor_user_id?: string
  actor_api_key_id?: string
  action?: string
  entity_type?: string
  entity_id?: string
}

export const auditApi = {
  list(filters: AuditLogFilters = {}) {
    return api.get<PageResponse<AuditLogRead>>('/audit-logs', { params: filters })
  },
}
