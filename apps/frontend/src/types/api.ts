// ── Common ──────────────────────────────────────────────
export interface ApiMessage {
  message: string
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
  color: string
  usage_count: number
  created_at: string
}

export interface TagCreate {
  name: string
  color?: string
}

export interface TagUpdate {
  name?: string
  color?: string
}

// ── Ideas ───────────────────────────────────────────────
export interface IdeaRead {
  id: string
  title: string
  description: string
  status: string
  priority: string
  tags: TagRead[]
  creator: EntityRef
  linked_project: string | null
  linked_project_url: string | null
  created_at: string
  updated_at: string
}

export interface IdeaCreate {
  title: string
  description?: string
  priority?: string
  tag_ids?: string[]
}

export interface IdeaUpdate {
  title?: string
  description?: string
  priority?: string
}

export interface IdeaStatusUpdate {
  status: string
}

// ── Projects ────────────────────────────────────────────
export interface ProjectRead {
  id: string
  key: string
  name: string
  description: string
  status: string
  owner: EntityRef
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
  description?: string
  status?: string
  start_date?: string
  target_end_date?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
  status?: string
  start_date?: string
  target_end_date?: string
}

// ── Tasks ───────────────────────────────────────────────
export interface TaskRead {
  id: string
  project_id: string
  title: string
  description: string
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
  description?: string
  status?: string
  assignee_id?: string
  start_date?: string
  end_date?: string
}

export interface TaskUpdate {
  title?: string
  description?: string
  status?: string
  assignee_id?: string | null
  start_date?: string | null
  end_date?: string | null
}

// ── Gantt ───────────────────────────────────────────────
export interface GanttTask {
  id: string
  title: string
  status: string
  assignee: EntityRef | null
  start_date: string | null
  end_date: string | null
  progress: number
  version: number
}

export interface GanttDependency {
  id: string
  predecessor_id: string
  successor_id: string
}

export interface GanttRead {
  project: ProjectRead
  tasks: GanttTask[]
  dependencies: GanttDependency[]
}

export interface GanttBulkUpdate {
  tasks: Array<{
    id: string
    start_date?: string | null
    end_date?: string | null
    progress?: number
    status?: string
  }>
  dependencies?: Array<{
    id?: string
    predecessor_id: string
    successor_id: string
    _deleted?: boolean
  }>
}

export interface TaskDependencyCreate {
  predecessor_id: string
  successor_id: string
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
  allowed_entities?: string[]
}

export interface ApiKeyUpdate {
  name?: string
  is_active?: boolean
  scopes?: string[]
  allowed_entities?: string[]
}

// ── External Links ──────────────────────────────────────
export interface ExternalLinkRead {
  id: string
  entity_type: string
  entity_id: string
  url: string
  title: string
  link_type: string
  created_at: string
}

export interface ExternalLinkCreate {
  url: string
  title?: string
  link_type?: string
}

export interface LinkPreview {
  url: string
  title: string | null
  description: string | null
  image: string | null
}
