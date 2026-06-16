/// <reference lib="dom" />
/// <reference types="vite/client" />

declare const window: Window & typeof globalThis

declare module 'jordium-gantt-vue3' {
  import type { DefineComponent } from 'vue'

  export interface Task {
    id: number
    name: string
    predecessor?: number[]
    assignee?: string | string[]
    assigneeName?: string
    startDate?: string
    endDate?: string
    progress?: number
    parentId?: number
    children?: Task[]
    type?: string
    description?: string
    isEditable?: boolean
    barColor?: string
    [key: string]: unknown
  }

  export const GanttChart: DefineComponent<Record<string, unknown>>
  export const TaskListColumn: DefineComponent<Record<string, unknown>>
}
