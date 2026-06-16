<script setup lang="ts">
import { computed } from 'vue'

import { useWorkspaceStore } from '@/stores/workspace'

const store = useWorkspaceStore()
const days = computed(() => Array.from({ length: 24 }, (_, index) => index + 1))
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
            v-for="task in store.tasks"
            :key="task.id"
            :title="task.title"
            :subtitle="`${task.assignee} · ${task.progress}%`"
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
        <div v-for="task in store.tasks" :key="task.id" class="gantt-row">
          <div
            class="gantt-bar"
            :style="{ gridColumn: `${task.startDay + 1} / span ${task.duration}` }"
          >
            <div class="gantt-progress" :style="{ width: `${task.progress}%` }" />
          </div>
        </div>
      </div>
    </div>
  </v-card>
</template>

