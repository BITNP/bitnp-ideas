export type GlobalRole = 'superuser' | 'administrator' | 'developer'
export type IdeaStatus = 'active' | 'paused' | 'in_progress' | 'completed'
export type ProjectStatus = 'planning' | 'active' | 'paused' | 'completed' | 'cancelled'
export type TaskStatus = 'todo' | 'in_progress' | 'blocked' | 'review' | 'done' | 'cancelled'
export type Priority = 'low' | 'medium' | 'high'

export interface EntityRef {
  id: string
  name: string
}

export interface IdeaSummary {
  id: string
  title: string
  status: IdeaStatus
  priority: Priority
  tags: string[]
  updatedAt: string
}

export interface ProjectSummary {
  id: string
  key: string
  name: string
  status: ProjectStatus
  progress: number
}

export interface TaskSummary {
  id: string
  projectId: string
  title: string
  status: TaskStatus
  assignee?: EntityRef
  startDate?: string
  endDate?: string
  progress: number
  version: number
}

