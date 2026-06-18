// ── Common ──────────────────────────────────────────────
export interface ApiMessage {
  message: string
}

export interface PaginationParams {
  offset?: number
  limit?: number
}

export interface PageResponse<T> {
  data: T[]
  total: number
}

export interface EntityRef {
  id: string
  name: string
}

// ── Auth ────────────────────────────────────────────────
export interface CurrentUser {
  id: string
  email: string
  display_name: string
  global_role: 'superuser' | 'administrator' | 'developer'
  is_active: boolean
}

export interface LoginResponse {
  authorization_url: string
  state: string
}

export interface CallbackResponse {
  access_token: string
  token_type: string
  user: CurrentUser
}

// ── Tags ────────────────────────────────────────────────
export interface TagRead {
  id: string
  name: string
  slug: string
  color: string | null
  description: string | null
  is_active: boolean
  usage_count: number
  created_at: string
}

export interface TagCreate {
  name: string
  color?: string | null
  description?: string | null
}

export interface TagUpdate {
  name?: string | null
  color?: string | null
  description?: string | null
  is_active?: boolean | null
}

// ── Ideas ───────────────────────────────────────────────
export interface IdeaRead {
  id: string
  title: string
  description: string | null
  status: string
  priority: string | null
  tags: TagRead[]
  creator: EntityRef
  linked_project: EntityRef | null
  linked_project_url: string | null
  created_at: string
  updated_at: string
}

export interface IdeaCreate {
  title: string
  description?: string | null
  priority?: string | null
  tag_names?: string[]
}

export interface IdeaUpdate {
  title?: string | null
  description?: string | null
  priority?: string | null
  linked_project_id?: string | null
  linked_project_url?: string | null
}

export interface IdeaStatusUpdate {
  status: string
  note?: string | null
  linked_project_id?: string | null
  linked_project_url?: string | null
}

export interface IdeaStatusHistoryRead {
  id: string
  idea_id: string
  from_status: string | null
  to_status: string
  actor_id: string | null
  note: string | null
  linked_project_id: string | null
  linked_project_url: string | null
  created_at: string
}

// ── Projects ────────────────────────────────────────────
export interface ProjectRead {
  id: string
  key: string
  name: string
  description: string | null
  status: string
  owner: EntityRef | null
  progress: number
  start_date: string | null
  target_end_date: string | null
  members: EntityRef[]
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  key: string
  name: string
  description?: string | null
  owner_id?: string | null
}

export interface ProjectUpdate {
  key?: string | null
  name?: string | null
  description?: string | null
  status?: string | null
  owner_id?: string | null
  start_date?: string | null
  target_end_date?: string | null
}

// ── Tasks ───────────────────────────────────────────────
export interface TaskRead {
  id: string
  project_id: string
  title: string
  description: string | null
  status: string
  assignee: EntityRef | null
  start_date: string | null
  end_date: string | null
  progress: number
  version: number
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  description?: string | null
  assignee_id?: string | null
  start_date?: string | null
  end_date?: string | null
}

export interface TaskUpdate {
  title?: string | null
  description?: string | null
  status?: string | null
  assignee_id?: string | null
  start_date?: string | null
  end_date?: string | null
  progress?: number | null
  parent_task_id?: string | null
  version?: number | null
}

// ── Gantt ───────────────────────────────────────────────
export interface GanttDependency {
  id: string
  predecessor_task_id: string
  successor_task_id: string
  dependency_type: 'finish_to_start'
}

export interface GanttRead {
  project: ProjectRead
  tasks: TaskRead[]
  dependencies: GanttDependency[]
}

export interface GanttBulkChange {
  task_id: string
  version: number
  start_date?: string | null
  end_date?: string | null
  assignee_id?: string | null
  progress?: number | null
  status?: string | null
}

export interface GanttBulkUpdate {
  changes: GanttBulkChange[]
}

export interface TaskDependencyCreate {
  predecessor_task_id: string
  successor_task_id: string
  dependency_type?: 'finish_to_start'
}

// ── Activity ────────────────────────────────────────────
export interface ActivityRead {
  id: string
  project_id: string
  actor: EntityRef | null
  action_type: string
  entity_type: string
  entity_id: string
  before: Record<string, unknown> | null
  after: Record<string, unknown> | null
  created_at: string
}

export interface AuditLogRead {
  id: string
  actor_user_id: string | null
  actor_api_key_id: string | null
  action: string
  entity_type: string
  entity_id: string | null
  before: Record<string, unknown> | null
  after: Record<string, unknown> | null
  metadata: Record<string, unknown> | null
  created_at: string
}

// ── API Keys ────────────────────────────────────────────
export interface ApiKeyRead {
  id: string
  name: string
  key_id: string
  secret_last4: string
  scopes: string[]
  allowed_entities: string[]
  is_active: boolean
  last_used_at: string | null
  created_at: string
}

export interface ApiKeyCreate {
  name: string
  scopes?: string[]
}

export interface ApiKeyUpdate {
  name?: string | null
  is_active?: boolean | null
  scopes?: string[] | null
}

export interface ApiKeyCreateResponse {
  api_key: ApiKeyRead
  secret: string
}

// ── External Links ──────────────────────────────────────
export interface ExternalLinkRead {
  id: string
  entity_type: string
  entity_id: string
  url: string
  title: string | null
  description: string | null
  image_url: string | null
  site_name: string | null
  link_type: string | null
  created_at: string
}

export type ExternalLinkEntityType = 'idea' | 'project' | 'task'

export interface ExternalLinkCreate {
  url: string
  title?: string | null
  description?: string | null
  link_type?: string | null
}

export interface LinkPreview {
  url: string
  title: string | null
  description: string | null
  image: string | null
}
