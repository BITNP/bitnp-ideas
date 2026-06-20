<script setup lang="ts">
import { computed, ref } from 'vue'
import { GanttChart, TaskListColumn } from 'jordium-gantt-vue3'
import type { Task as JordiumTask } from 'jordium-gantt-vue3'

import { ganttApi } from '@/api/modules'
import EmptyState from '@/components/EmptyState.vue'
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
  showCreateTaskAction?: boolean
}

interface GanttTaskRecord extends JordiumTask {
  sourceId: string
  sourceVersion: number
  sourceStatus: string
  statusLabel: string
  scheduleLabel: string
  progressLabel: string
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
  showCreateTaskAction: false,
})

const emit = defineEmits<{
  refresh: []
  error: [message: string]
  createTask: []
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
      statusLabel: formatStatus(task.status),
      scheduleLabel: getScheduleLabel(task),
      progressLabel: `${task.progress}%`,
      type: 'task',
      assignee: task.assignee?.id,
      assigneeName: task.assignee?.name ?? 'No owner',
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

const scheduledTaskCount = computed(() =>
  props.tasks.filter((task) => Boolean(task.start_date && task.end_date)).length,
)

const unscheduledTaskCount = computed(() => props.tasks.length - scheduledTaskCount.value)
const blockedTaskCount = computed(() => props.tasks.filter((task) => task.status === 'blocked').length)
const completedTaskCount = computed(() =>
  props.tasks.filter((task) => task.status === 'done' || task.progress >= 100).length,
)

const planSummary = computed(() => [
  { label: 'Tasks', value: props.tasks.length, color: 'primary' },
  { label: 'Scheduled', value: scheduledTaskCount.value, color: 'success' },
  { label: 'Unscheduled', value: unscheduledTaskCount.value, color: unscheduledTaskCount.value > 0 ? 'warning' : 'default' },
  { label: 'Blocked', value: blockedTaskCount.value, color: blockedTaskCount.value > 0 ? 'error' : 'default' },
  { label: 'Done', value: completedTaskCount.value, color: 'success' },
  { label: 'Dependencies', value: props.dependencies.length, color: 'secondary' },
])

const statusLegend = computed(() => [
  { label: 'Todo', color: getStatusColor('todo', 0) },
  { label: 'In progress', color: getStatusColor('in_progress', 25) },
  { label: 'Review', color: getStatusColor('review', 75) },
  { label: 'Blocked', color: getStatusColor('blocked', 10) },
  { label: 'Done', color: getStatusColor('done', 100) },
])

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

function formatStatus(status: string): string {
  return status.replace(/_/g, ' ')
}

function formatShortDate(value: string | null): string | null {
  if (!value) return null
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function getScheduleLabel(task: BoardTask): string {
  const start = formatShortDate(task.start_date)
  const end = formatShortDate(task.end_date)
  if (start && end) return `${start} - ${end}`
  if (start) return `Starts ${start}`
  if (end) return `Due ${end}`
  return 'Not scheduled'
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
    <v-card-title class="gantt-header">
      <div>
        <div class="text-h6">{{ compact ? 'Plan snapshot' : 'Project plan' }}</div>
        <div v-if="!compact" class="text-body-2 text-medium-emphasis">
          Timeline, ownership, dependencies, and delivery risk.
        </div>
      </div>
      <div class="gantt-header-actions">
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
        <v-chip v-if="readonly && !compact" color="default" size="small" variant="tonal">Read only</v-chip>
        <v-chip v-if="saving" color="primary" size="small" variant="tonal">Saving</v-chip>
      </div>
    </v-card-title>
    <v-divider />

    <div v-if="chartTasks.length" class="gantt-meta">
      <div class="gantt-summary" data-test="gantt-summary">
        <v-chip
          v-for="item in planSummary"
          :key="item.label"
          :color="item.color"
          size="small"
          variant="tonal"
        >
          {{ item.label }} {{ item.value }}
        </v-chip>
      </div>
      <div v-if="!compact" class="gantt-legend" aria-label="Task status legend">
        <span v-for="item in statusLegend" :key="item.label" class="gantt-legend-item">
          <span class="gantt-legend-dot" :style="{ backgroundColor: item.color }" />
          {{ item.label }}
        </span>
      </div>
    </div>

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
        <TaskListColumn v-if="!compact" prop="statusLabel" label="Status" :width="108" />
        <TaskListColumn prop="assigneeName" label="Owner" :width="140" />
        <TaskListColumn v-if="!compact" prop="scheduleLabel" label="Window" :width="136" />
        <TaskListColumn prop="progressLabel" label="Progress" :width="92" align="center" />
      </GanttChart>
    </div>

    <EmptyState
      v-else
      icon="$gantt"
      title="No scheduled tasks yet"
      description="Add project tasks with start and end dates to build the plan timeline."
      :action-label="showCreateTaskAction && !readonly ? 'Add task' : undefined"
      @action="emit('createTask')"
    />
  </v-card>
</template>

<style scoped>
.gantt-card {
  overflow: hidden;
}

.gantt-header {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.gantt-header-actions,
.gantt-summary,
.gantt-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.gantt-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
}

.gantt-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  color: rgba(var(--v-theme-on-surface), 0.72);
}

.gantt-legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.jordium-gantt-host {
  min-height: 260px;
  width: 100%;
  overflow: hidden;
}

@media (max-width: 720px) {
  .gantt-meta {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
