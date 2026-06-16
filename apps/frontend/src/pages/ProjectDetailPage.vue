<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import GanttBoard from '@/components/GanttBoard.vue'
import MetricTile from '@/components/MetricTile.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const route = useRoute()
const store = useWorkspaceStore()
const tab = ref(route.name === 'project-gantt' ? 'gantt' : route.name === 'project-activity' ? 'activity' : 'overview')
const project = computed(() => store.projects.find((item) => item.id === route.params.id) ?? store.projects[0])
</script>

<template>
  <div class="page-shell">
    <div class="toolbar-row mb-4">
      <div>
        <div class="text-caption text-medium-emphasis">{{ project.key }}</div>
        <h1 class="text-h5 mb-1">{{ project.name }}</h1>
      </div>
      <v-btn color="primary" prepend-icon="$plus">Add task</v-btn>
    </div>

    <v-tabs v-model="tab" class="mb-4">
      <v-tab value="overview">Overview</v-tab>
      <v-tab value="tasks">Tasks</v-tab>
      <v-tab value="gantt">Gantt</v-tab>
      <v-tab value="ideas">Ideas</v-tab>
      <v-tab value="links">Links</v-tab>
      <v-tab value="activity">Activity</v-tab>
      <v-tab value="settings">Settings</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <v-window-item value="overview">
        <div class="metric-grid mb-4">
          <MetricTile label="Progress" :value="`${project.progress}%`" icon="$check" tone="success" />
          <MetricTile label="Members" :value="project.members.length" icon="$users" tone="secondary" />
          <MetricTile label="Open tasks" :value="store.openTasks" icon="$calendar" tone="primary" />
          <MetricTile label="Linked ideas" :value="1" icon="$idea" tone="accent" />
        </div>
        <div class="content-grid">
          <v-card border flat>
            <v-card-title>Tasks</v-card-title>
            <v-list lines="two">
              <v-list-item
                v-for="task in store.tasks"
                :key="task.id"
                :title="task.title"
                :subtitle="`${task.assignee} · ${task.status}`"
                prepend-icon="$calendar"
              />
            </v-list>
          </v-card>
          <v-card border flat>
            <v-card-title>Members</v-card-title>
            <v-list>
              <v-list-item v-for="member in project.members" :key="member" :title="member" prepend-icon="$account" />
            </v-list>
          </v-card>
        </div>
      </v-window-item>

      <v-window-item value="tasks">
        <v-card border flat>
          <v-table>
            <thead>
              <tr>
                <th>Task</th>
                <th>Assignee</th>
                <th>Status</th>
                <th>Progress</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="task in store.tasks" :key="task.id">
                <td>{{ task.title }}</td>
                <td>{{ task.assignee }}</td>
                <td>{{ task.status }}</td>
                <td><v-slider :model-value="task.progress" hide-details density="compact" /></td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-window-item>

      <v-window-item value="gantt">
        <GanttBoard />
      </v-window-item>

      <v-window-item value="ideas">
        <v-card border flat>
          <v-list lines="two">
            <v-list-item
              v-for="idea in store.ideas"
              :key="idea.id"
              :title="idea.title"
              :subtitle="idea.status"
              prepend-icon="$idea"
            />
          </v-list>
        </v-card>
      </v-window-item>

      <v-window-item value="links">
        <v-card border flat>
          <v-list>
            <v-list-item
              title="BITNP Keycloak Account Service"
              subtitle="https://github.com/BITNP/keycloak-account-service"
              prepend-icon="$link"
            />
          </v-list>
        </v-card>
      </v-window-item>

      <v-window-item value="activity">
        <v-card border flat>
          <v-timeline side="end" density="compact">
            <v-timeline-item dot-color="primary" size="small">
              <div class="font-weight-medium">task.rescheduled</div>
              <div class="text-body-2 text-medium-emphasis">Devon updated task_idea_api end date.</div>
            </v-timeline-item>
            <v-timeline-item dot-color="secondary" size="small">
              <div class="font-weight-medium">idea.linked</div>
              <div class="text-body-2 text-medium-emphasis">Alice linked the Gantt dependency idea.</div>
            </v-timeline-item>
          </v-timeline>
        </v-card>
      </v-window-item>

      <v-window-item value="settings">
        <v-card border flat>
          <v-card-title>Project settings</v-card-title>
          <v-card-text>
            <v-text-field label="Project name" :model-value="project.name" />
            <v-select label="Status" :items="['planning', 'active', 'paused', 'completed', 'cancelled']" :model-value="project.status" />
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>
  </div>
</template>

