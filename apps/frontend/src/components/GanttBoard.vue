<script setup lang="ts">
import { computed, ref } from 'vue'
import { GanttChart, TaskListColumn } from 'jordium-gantt-vue3'
import type { Task as JordiumTask } from 'jordium-gantt-vue3'

import { ganttApi } from '@/api/modules'
import type { GanttDependency, TaskRead } from '@/types/api'

type BoardTask = TaskRead & {
  project_id?: string
}

interface Props {
  tasks: BoardTask[]
  dependencies?: GanttDependency[]
  projectId?: string
  readonly?: boolean
  compact?: boolean
}

interface GanttTaskRecord extends JordiumTask {
  sourceId: string
  sourceVersion: number
  sourceStatus: string
}

interface TaskUpdatedEvent {
  task: JordiumTask
}

interface LinkAddedEvent {
  targetTask: JordiumTask
  newTask: JordiumTask
}

interface LinkDeletedEvent {
  sourceTaskId: number
  targetTaskId: number
}

const props = withDefaults(defineProps<Props>(), {
  dependencies: () => [],
  projectId: undefined,
  readonly: false,
  compact: false,
})

const emit = defineEmits<{
  refresh: []
  error: [message: string]
}>()

const saving = ref(false)
const selectedScale = ref<'day' | 'week' | 'month'>(props.compact ? 'month' : 'week')
const scaleOptions = [
  { label: 'Day', value: 'day' },
  { label: 'Week', value: 'week' },
  { label: 'Month', value: 'month' },
]

const idMaps = computed(() => {
  const uuidToGanttId = new Map<string, number>()
  const ganttIdToUuid = new Map<number, string>()

  props.tasks.forEach((task, index) => {
    const ganttId = index + 1
    uuidToGanttId.set(task.id, ganttId)
    ganttIdToUuid.set(ganttId, task.id)
  })

  return { uuidToGanttId, ganttIdToUuid }
})

const taskDependencies = computed(() => {
  const map = new Map<string, number[]>()

  for (const dependency of props.dependencies) {
    const predecessorUuid = dependency.predecessor_task_id
    const successorUuid = dependency.successor_task_id
    const predecessorId = idMaps.value.uuidToGanttId.get(predecessorUuid)

    if (!predecessorId) continue

    const current = map.get(successorUuid) ?? []
    current.push(predecessorId)
    map.set(successorUuid, current)
  }

  return map
})

const chartTasks = computed<GanttTaskRecord[]>(() =>
  props.tasks.map((task) => {
    const ganttId = idMaps.value.uuidToGanttId.get(task.id)
    const statusColor = getStatusColor(task.status, task.progress)

    return {
      id: ganttId ?? 0,
      sourceId: task.id,
      sourceVersion: task.version,
      sourceStatus: task.status,
      name: task.title,
      type: 'task',
      assignee: task.assignee?.id,
      assigneeName: task.assignee?.name ?? 'Unassigned',
      startDate: task.start_date ?? undefined,
      endDate: task.end_date ?? undefined,
      progress: task.progress,
      predecessor: taskDependencies.value.get(task.id) ?? [],
      description: getTaskDescription(task),
      barColor: statusColor,
      isEditable: !props.readonly,
    }
  }),
)

const assigneeOptions = computed(() => {
  const options = new Map<string, { value: string; label: string }>()

  for (const task of props.tasks) {
    if (task.assignee) {
      options.set(task.assignee.id, {
        value: task.assignee.id,
        label: task.assignee.name,
      })
    }
  }

  return Array.from(options.values())
})

const chartHeight = computed(() => {
  if (props.compact) {
    return props.tasks.length > 0 ? 420 : 260
  }

  return Math.max(540, Math.min(820, props.tasks.length * 52 + 180))
})

function getStatusColor(status: string, progress: number): string {
  if (status === 'done' || status === 'completed' || progress >= 100) return '#5b8c5a'
  if (status === 'blocked') return '#b15c4b'
  if (status === 'review') return '#8b6f47'
  if (status === 'in_progress') return '#3f6f8f'
  return '#6f7785'
}

function getTaskDescription(task: BoardTask): string | undefined {
  return 'description' in task ? task.description ?? undefined : undefined
}

function resolveUuid(ganttId: unknown): string | null {
  if (typeof ganttId !== 'number') return null
  return idMaps.value.ganttIdToUuid.get(ganttId) ?? null
}

function findDependency(predecessorTaskId: string, successorTaskId: string): GanttDependency | undefined {
  return props.dependencies.find(
    (dependency) =>
      dependency.predecessor_task_id === predecessorTaskId &&
      dependency.successor_task_id === successorTaskId,
  )
}

async function persistTaskSchedule(task: JordiumTask) {
  if (!props.projectId || props.readonly) return

  const sourceId = resolveUuid(task.id)
  const sourceTask = props.tasks.find((item) => item.id === sourceId)

  if (!sourceId || !sourceTask) return

  saving.value = true
  try {
    await ganttApi.bulkUpdate(props.projectId, {
      changes: [
        {
          task_id: sourceId,
          version: sourceTask.version,
          start_date: task.startDate ?? null,
          end_date: task.endDate ?? null,
          progress: typeof task.progress === 'number' ? task.progress : sourceTask.progress,
        },
      ],
    })
    emit('refresh')
  } catch {
    emit('error', 'Failed to save gantt schedule changes.')
  } finally {
    saving.value = false
  }
}

async function persistAddedDependency(predecessorGanttId: unknown, successorGanttId: unknown) {
  if (!props.projectId || props.readonly) return

  const predecessorTaskId = resolveUuid(predecessorGanttId)
  const successorTaskId = resolveUuid(successorGanttId)

  if (!predecessorTaskId || !successorTaskId) return
  if (findDependency(predecessorTaskId, successorTaskId)) return

  saving.value = true
  try {
    await ganttApi.addDependency(props.projectId, {
      predecessor_task_id: predecessorTaskId,
      successor_task_id: successorTaskId,
      dependency_type: 'finish_to_start',
    })
    emit('refresh')
  } catch {
    emit('error', 'Failed to save task dependency.')
  } finally {
    saving.value = false
  }
}

async function persistDeletedDependency(event: LinkDeletedEvent) {
  if (!props.projectId || props.readonly) return

  const predecessorTaskId = resolveUuid(event.sourceTaskId)
  const successorTaskId = resolveUuid(event.targetTaskId)

  if (!predecessorTaskId || !successorTaskId) return

  const dependency = findDependency(predecessorTaskId, successorTaskId)
  if (!dependency) return

  saving.value = true
  try {
    await ganttApi.removeDependency(props.projectId, dependency.id)
    emit('refresh')
  } catch {
    emit('error', 'Failed to remove task dependency.')
  } finally {
    saving.value = false
  }
}

function handleTaskUpdated(event: TaskUpdatedEvent) {
  persistTaskSchedule(event.task)
}

function handleTaskbarChanged(task: JordiumTask) {
  persistTaskSchedule(task)
}

function handlePredecessorAdded(event: LinkAddedEvent) {
  persistAddedDependency(event.newTask.id, event.targetTask.id)
}

function handleSuccessorAdded(event: LinkAddedEvent) {
  persistAddedDependency(event.targetTask.id, event.newTask.id)
}
</script>

<template>
  <v-card border flat class="gantt-card">
    <v-card-title class="toolbar-row">
      <span>{{ compact ? 'Plan snapshot' : 'Project plan' }}</span>
      <v-btn-toggle
        v-if="!compact"
        v-model="selectedScale"
        mandatory
        density="compact"
        variant="outlined"
        divided
      >
        <v-btn
          v-for="option in scaleOptions"
          :key="option.value"
          :value="option.value"
          size="small"
        >
          {{ option.label }}
        </v-btn>
      </v-btn-toggle>
      <v-chip v-if="saving" color="primary" size="small" variant="tonal">Saving</v-chip>
    </v-card-title>
    <v-divider />

    <div v-if="chartTasks.length" class="jordium-gantt-host" :style="{ height: `${chartHeight}px` }">
      <GanttChart
        :tasks="chartTasks"
        :show-toolbar="!compact"
        :use-default-drawer="false"
        :use-default-milestone-dialog="false"
        :allow-drag-and-resize="!readonly"
        :enable-link-anchor="!readonly"
        :enable-task-row-move="false"
        :enable-task-list-context-menu="false"
        :enable-task-bar-context-menu="false"
        :assignee-options="assigneeOptions"
        :locale="'en-US'"
        :theme="'light'"
        :time-scale="selectedScale"
        :row-height="44"
        task-list-column-render-mode="declarative"
        @task-updated="handleTaskUpdated"
        @taskbar-drag-end="handleTaskbarChanged"
        @taskbar-resize-end="handleTaskbarChanged"
        @predecessor-added="handlePredecessorAdded"
        @successor-added="handleSuccessorAdded"
        @link-deleted="persistDeletedDependency"
      >
        <TaskListColumn prop="name" label="Task" :width="260" />
        <TaskListColumn prop="assigneeName" label="Owner" :width="140" />
        <TaskListColumn prop="progress" label="Progress" :width="92" align="center" />
      </GanttChart>
    </div>

    <v-card-text v-else class="text-medium-emphasis">
      No scheduled tasks yet.
    </v-card-text>
  </v-card>
</template>

<style scoped>
.gantt-card {
  overflow: hidden;
}

.jordium-gantt-host {
  min-height: 260px;
  width: 100%;
  overflow: hidden;
}
</style>
