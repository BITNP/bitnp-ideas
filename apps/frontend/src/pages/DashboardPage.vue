<script setup lang="ts">
import GanttBoard from '@/components/GanttBoard.vue'
import MetricTile from '@/components/MetricTile.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const store = useWorkspaceStore()
</script>

<template>
  <div class="page-shell">
    <div class="toolbar-row mb-4">
      <div>
        <h1 class="text-h5 mb-1">Execution Overview</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">Idea intake, project delivery, and traceable execution.</p>
      </div>
      <v-btn color="primary" prepend-icon="$plus" to="/ideas">New idea</v-btn>
    </div>

    <div class="metric-grid mb-4">
      <MetricTile label="Active ideas" :value="store.activeIdeas" icon="$idea" tone="primary" />
      <MetricTile label="Active projects" :value="store.activeProjects" icon="$gantt" tone="secondary" />
      <MetricTile label="Open tasks" :value="store.openTasks" icon="$calendar" tone="accent" />
      <MetricTile label="Audit coverage" value="100%" icon="$activity" tone="success" />
    </div>

    <div class="content-grid">
      <GanttBoard />

      <v-card border flat>
        <v-card-title>Recent activity</v-card-title>
        <v-list lines="two">
          <v-list-item
            title="Devon rescheduled idea API work"
            subtitle="task.rescheduled · IDEAS MVP"
            prepend-icon="$activity"
          />
          <v-list-item
            title="Alice linked a Gantt dependency idea"
            subtitle="idea.linked · IDEAS MVP"
            prepend-icon="$link"
          />
          <v-list-item
            title="AI intake workflow key is active"
            subtitle="api_key.created · idea-only scopes"
            prepend-icon="$key"
          />
        </v-list>
      </v-card>
    </div>
  </div>
</template>

