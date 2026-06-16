import { defineStore } from 'pinia'
import type { IdeaStatus, ProjectStatus, TaskStatus } from '@bitnp-ideas/shared-types'

interface TagItem {
  id: string
  name: string
  slug: string
  color: string
  usageCount: number
}

interface IdeaItem {
  id: string
  title: string
  description: string
  status: IdeaStatus
  priority: 'low' | 'medium' | 'high'
  tags: TagItem[]
  creator: string
  updatedAt: string
}

interface ProjectItem {
  id: string
  key: string
  name: string
  status: ProjectStatus
  progress: number
  members: string[]
}

interface TaskItem {
  id: string
  title: string
  status: TaskStatus
  assignee: string
  startDay: number
  duration: number
  progress: number
}

export const useWorkspaceStore = defineStore('workspace', {
  state: () => ({
    density: 'comfortable',
    tags: [
      { id: 'tag_ai', name: 'ai', slug: 'ai', color: '#3F51B5', usageCount: 8 },
      { id: 'tag_backend', name: 'backend', slug: 'backend', color: '#00897B', usageCount: 6 },
      { id: 'tag_gantt', name: 'gantt', slug: 'gantt', color: '#F4511E', usageCount: 3 },
    ] as TagItem[],
    ideas: [
      {
        id: 'idea_ai_ingestion',
        title: 'Add AI workflow idea ingestion',
        description: 'Signed API clients can submit ideas without touching projects or tasks.',
        status: 'active',
        priority: 'high',
        tags: [],
        creator: 'Devon Developer',
        updatedAt: '2026-06-16',
      },
      {
        id: 'idea_dependency_drag',
        title: 'Drag dependency lines on the Gantt view',
        description: 'Create finish-to-start dependencies directly from the scheduling canvas.',
        status: 'in_progress',
        priority: 'medium',
        tags: [],
        creator: 'Alice Admin',
        updatedAt: '2026-06-16',
      },
    ] as IdeaItem[],
    projects: [
      {
        id: 'prj_ideas',
        key: 'IDEAS',
        name: 'IDEAS MVP',
        status: 'active',
        progress: 38,
        members: ['Alice Admin', 'Devon Developer'],
      },
    ] as ProjectItem[],
    tasks: [
      {
        id: 'task_bootstrap',
        title: 'Bootstrap monorepo',
        status: 'done',
        assignee: 'Alice Admin',
        startDay: 0,
        duration: 2,
        progress: 100,
      },
      {
        id: 'task_idea_api',
        title: 'Implement idea and tag API',
        status: 'in_progress',
        assignee: 'Devon Developer',
        startDay: 3,
        duration: 7,
        progress: 45,
      },
      {
        id: 'task_gantt',
        title: 'Build Gantt scheduling surface',
        status: 'todo',
        assignee: 'Devon Developer',
        startDay: 11,
        duration: 11,
        progress: 10,
      },
    ] as TaskItem[],
  }),
  getters: {
    activeIdeas: (state) => state.ideas.filter((idea) => idea.status === 'active').length,
    activeProjects: (state) => state.projects.filter((project) => project.status === 'active').length,
    openTasks: (state) => state.tasks.filter((task) => task.status !== 'done').length,
  },
  actions: {
    attachTags() {
      this.ideas[0].tags = [this.tags[0], this.tags[1]]
      this.ideas[1].tags = [this.tags[2]]
    },
  },
})

