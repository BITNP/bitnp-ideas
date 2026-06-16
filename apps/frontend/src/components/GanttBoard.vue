<script setup lang="ts">
import { computed } from 'vue'
import type { GanttTask, GanttDependency } from '@/types/api'

interface Props {
  tasks: GanttTask[]
  dependencies?: GanttDependency[]
}
const props = withDefaults(defineProps<Props>(), { dependencies: () => [] })

interface TaskBar {
  id: string
  startColumn: number
  duration: number
  progress: number
}

const timelineInfo = computed(() => {
  const allDates: Date[] = []
  for (const t of props.tasks) {
    if (t.start_date) allDates.push(new Date(t.start_date))
    if (t.end_date) allDates.push(new Date(t.end_date))
  }
  if (allDates.length === 0) {
    return { startDate: new Date(), totalDays: 24 }
  }
  let min = allDates[0]!
  let max = allDates[0]!
  for (const d of allDates) {
    if (d < min) min = d
    if (d > max) max = d
  }
  const pad = 2
  const startDate = new Date(min)
  startDate.setDate(startDate.getDate() - pad)
  const endDate = new Date(max)
  endDate.setDate(endDate.getDate() + pad)
  const totalDays = Math.round((endDate.getTime() - startDate.getTime()) / 86400000) + 1
  return { startDate, totalDays }
})

const days = computed(() => Array.from({ length: timelineInfo.value.totalDays }, (_, i) => i + 1))

const taskBars = computed<TaskBar[]>(() => {
  const { startDate } = timelineInfo.value
  return props.tasks.map((task) => {
    if (task.start_date && task.end_date) {
      const sd = new Date(task.start_date)
      const ed = new Date(task.end_date)
      const startColumn = Math.round((sd.getTime() - startDate.getTime()) / 86400000) + 1
      const duration = Math.round((ed.getTime() - sd.getTime()) / 86400000) + 1
      return { id: task.id, startColumn, duration, progress: task.progress }
    }
    return { id: task.id, startColumn: 1, duration: 1, progress: task.progress }
  })
})
</script>

<template>
  <v-card border flat>
    <v-card-title class="toolbar-row">
      <span>Gantt schedule</span>
      <v-btn-toggle density="compact" mandatory model-value="day" variant="outlined">
        <v-btn value="day">Day</v-btn>
        <v-btn value="week">Week</v-btn>
        <v-btn value="month">Month</v-btn>
      </v-btn-toggle>
    </v-card-title>
    <v-divider />

    <div class="gantt-grid">
      <div>
        <div class="pa-3 text-caption text-medium-emphasis">Task</div>
        <v-list density="compact">
          <v-list-item
            v-for="task in props.tasks"
            :key="task.id"
            :title="task.title"
            :subtitle="`${task.assignee?.name ?? 'Unassigned'} · ${task.progress}%`"
            min-height="48"
          >
            <template #prepend>
              <v-icon :color="task.status === 'done' ? 'success' : 'primary'" icon="$check" />
            </template>
          </v-list-item>
        </v-list>
      </div>

      <div>
        <div class="gantt-row text-caption text-medium-emphasis">
          <div v-for="day in days" :key="day" class="text-center">{{ day }}</div>
        </div>
        <div v-for="bar in taskBars" :key="bar.id" class="gantt-row">
          <div
            class="gantt-bar"
            :style="{ gridColumn: `${bar.startColumn} / span ${bar.duration}` }"
          >
            <div class="gantt-progress" :style="{ width: `${bar.progress}%` }" />
          </div>
        </div>
      </div>
    </div>
  </v-card>
</template>
