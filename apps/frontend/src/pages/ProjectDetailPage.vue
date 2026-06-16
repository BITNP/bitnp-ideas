<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { VDateInput } from 'vuetify/components/VDateInput'

import GanttBoard from '@/components/GanttBoard.vue'
import MetricTile from '@/components/MetricTile.vue'
import { projectsApi, tasksApi, ganttApi, activityApi, linksApi } from '@/api/modules'
import type { ProjectRead, TaskRead, GanttRead, ActivityRead, IdeaRead, ExternalLinkRead } from '@/types/api'

const route = useRoute()
const projectId = route.params.id as string

const tab = ref(route.name === 'project-gantt' ? 'gantt' : route.name === 'project-activity' ? 'activity' : 'overview')

const project = ref<ProjectRead | null>(null)
const tasks = ref<Array<TaskRead | GanttRead['tasks'][number]>>([])
const ganttData = ref<GanttRead | null>(null)
const activities = ref<ActivityRead[]>([])
const projectIdeas = ref<IdeaRead[]>([])
const links = ref<ExternalLinkRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const openTaskCount = computed(() => tasks.value.filter((t) => t.status !== 'done').length)

const addTaskDialog = ref(false)
const newTaskTitle = ref('')
const newTaskDescription = ref('')
const newTaskAssignee = ref('')
const taskDateRange = ref<Date[]>([])

const settingsName = ref('')
const settingsStatus = ref('')
const settingsDescription = ref('')

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    const res = await projectsApi.get(projectId)
    project.value = res.data
    settingsName.value = res.data.name
    settingsStatus.value = res.data.status
    settingsDescription.value = res.data.description ?? ''
  } catch {
    error.value = 'Failed to load project.'
    loading.value = false
    return
  }

  try {
    const res = await tasksApi.list(projectId)
    tasks.value = res.data
  } catch {
    // tasks are optional for overview display
  }

  loading.value = false

  if (tab.value === 'gantt') {
    fetchGantt()
  } else if (tab.value === 'activity') {
    fetchActivities()
  } else if (tab.value === 'ideas') {
    fetchIdeas()
  } else if (tab.value === 'links') {
    fetchLinks()
  }
})

watch(tab, (newTab) => {
  if (newTab === 'tasks' && tasks.value.length === 0) {
    tasksApi.list(projectId).then((res) => { tasks.value = res.data }).catch(() => {})
  } else if (newTab === 'gantt' && !ganttData.value) {
    fetchGantt()
  } else if (newTab === 'activity' && activities.value.length === 0) {
    fetchActivities()
  } else if (newTab === 'ideas' && projectIdeas.value.length === 0) {
    fetchIdeas()
  } else if (newTab === 'links' && links.value.length === 0) {
    fetchLinks()
  }
})

async function fetchActivities() {
  try {
    const res = await activityApi.list(projectId)
    activities.value = res.data
  } catch { /* empty */ }
}

async function fetchIdeas() {
  try {
    const res = await projectsApi.listIdeas(projectId)
    projectIdeas.value = res.data
  } catch { /* empty */ }
}

async function fetchLinks() {
  try {
    const res = await linksApi.list('project', projectId)
    links.value = res.data
  } catch { /* empty */ }
}

async function fetchGantt() {
  try {
    const res = await ganttApi.get(projectId)
    ganttData.value = res.data
    tasks.value = res.data.tasks
  } catch {
    ganttData.value = null
  }
}

async function handleAddTask() {
  if (!newTaskTitle.value) return
  try {
    const res = await tasksApi.create(projectId, {
      title: newTaskTitle.value,
      description: newTaskDescription.value || undefined,
      assignee_id: newTaskAssignee.value || undefined,
      start_date: taskDateRange.value[0]?.toISOString().slice(0, 10) || undefined,
      end_date: taskDateRange.value[1]?.toISOString().slice(0, 10) || undefined,
    })
    tasks.value.push(res.data)
    addTaskDialog.value = false
    newTaskTitle.value = ''
    newTaskDescription.value = ''
    newTaskAssignee.value = ''
    taskDateRange.value = []
    if (ganttData.value) {
      fetchGantt()
    }
  } catch {
    error.value = 'Failed to create task.'
  }
}

async function handleSaveSettings() {
  if (!project.value) return
  try {
    const res = await projectsApi.update(projectId, {
      name: settingsName.value,
      status: settingsStatus.value,
      description: settingsDescription.value,
    })
    project.value = res.data
  } catch {
    error.value = 'Failed to update project settings.'
  }
}

function handleGanttError(message: string) {
  error.value = message
  fetchGantt()
}
</script>

<template>
  <div class="page-shell">
    <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = null">
      {{ error }}
    </v-alert>

    <template v-if="project">
      <div class="toolbar-row mb-4">
        <div>
          <div class="text-caption text-medium-emphasis">{{ project.key }}</div>
          <h1 class="text-h5 mb-1">{{ project.name }}</h1>
        </div>
        <v-btn color="primary" prepend-icon="$plus" @click="addTaskDialog = true">Add task</v-btn>
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
            <MetricTile label="Open tasks" :value="openTaskCount" icon="$calendar" tone="primary" />
            <MetricTile label="Linked ideas" :value="projectIdeas.length" icon="$idea" tone="accent" />
          </div>
          <div class="content-grid">
            <v-card border flat>
              <v-card-title>Tasks</v-card-title>
              <v-list v-if="tasks.length" lines="two">
                <v-list-item
                  v-for="task in tasks"
                  :key="task.id"
                  :title="task.title"
                  :subtitle="`${task.assignee?.name ?? '—'} · ${task.status}`"
                  prepend-icon="$calendar"
                />
              </v-list>
              <v-card-text v-else class="text-medium-emphasis">No tasks yet.</v-card-text>
            </v-card>
            <v-card border flat>
              <v-card-title>Members</v-card-title>
              <v-list v-if="project.members.length">
                <v-list-item
                  v-for="member in project.members"
                  :key="member.id"
                  :title="member.name"
                  prepend-icon="$account"
                />
              </v-list>
              <v-card-text v-else class="text-medium-emphasis">No members yet.</v-card-text>
            </v-card>
          </div>
        </v-window-item>

        <v-window-item value="tasks">
          <v-card v-if="tasks.length" border flat>
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
                <tr v-for="task in tasks" :key="task.id">
                  <td>{{ task.title }}</td>
                  <td>{{ task.assignee?.name ?? '—' }}</td>
                  <td>{{ task.status }}</td>
                  <td><v-slider :model-value="task.progress" hide-details density="compact" readonly /></td>
                </tr>
              </tbody>
            </v-table>
          </v-card>
          <v-card v-else border flat>
            <v-card-text class="text-medium-emphasis">No tasks yet.</v-card-text>
          </v-card>
        </v-window-item>

        <v-window-item value="gantt">
          <GanttBoard
            v-if="ganttData"
            :tasks="ganttData.tasks ?? []"
            :dependencies="ganttData.dependencies ?? []"
            :project-id="projectId"
            @refresh="fetchGantt"
            @error="handleGanttError"
          />
          <v-card v-else border flat>
            <v-card-text class="text-medium-emphasis">No gantt data available.</v-card-text>
          </v-card>
        </v-window-item>

        <v-window-item value="ideas">
          <v-card v-if="projectIdeas.length" border flat>
            <v-list lines="two">
              <v-list-item
                v-for="idea in projectIdeas"
                :key="idea.id"
                :title="idea.title"
                :subtitle="idea.status"
                prepend-icon="$idea"
              />
            </v-list>
          </v-card>
          <v-card v-else border flat>
            <v-card-text class="text-medium-emphasis">No linked ideas yet.</v-card-text>
          </v-card>
        </v-window-item>

        <v-window-item value="links">
          <v-card v-if="links.length" border flat>
            <v-list>
              <v-list-item
                v-for="link in links"
                :key="link.id"
                :title="link.title ?? link.url"
                :subtitle="link.url"
                prepend-icon="$link"
                :href="link.url"
                target="_blank"
              />
            </v-list>
          </v-card>
          <v-card v-else border flat>
            <v-card-text class="text-medium-emphasis">No links yet.</v-card-text>
          </v-card>
        </v-window-item>

        <v-window-item value="activity">
          <v-card v-if="activities.length" border flat>
            <v-timeline side="end" density="compact">
              <v-timeline-item
                v-for="activity in activities"
                :key="activity.id"
                dot-color="primary"
                size="small"
              >
                <div class="font-weight-medium">{{ activity.action_type }}</div>
                <div class="text-body-2 text-medium-emphasis">
                  {{ activity.actor?.name ?? 'System' }} · {{ new Date(activity.created_at).toLocaleString() }}
                </div>
              </v-timeline-item>
            </v-timeline>
          </v-card>
          <v-card v-else border flat>
            <v-card-text class="text-medium-emphasis">No activity yet.</v-card-text>
          </v-card>
        </v-window-item>

        <v-window-item value="settings">
          <v-card border flat>
            <v-card-title>Project settings</v-card-title>
            <v-card-text>
              <v-text-field v-model="settingsName" label="Project name" />
              <v-select
                v-model="settingsStatus"
                label="Status"
                :items="['planning', 'active', 'paused', 'completed', 'cancelled']"
              />
              <v-text-field v-model="settingsDescription" label="Description" />
              <v-btn color="primary" class="mt-2" @click="handleSaveSettings">Save</v-btn>
            </v-card-text>
          </v-card>
        </v-window-item>
      </v-window>
    </template>

    <div v-else-if="!loading" class="text-center py-8">
      <p class="text-body-1 text-medium-emphasis">Project not found.</p>
    </div>

    <v-dialog v-model="addTaskDialog" max-width="520">
      <v-card title="Add Task">
        <v-card-text>
          <v-text-field v-model="newTaskTitle" label="Title" />
          <v-textarea v-model="newTaskDescription" label="Description" rows="3" />
          <v-text-field v-model="newTaskAssignee" label="Assignee" />
          <v-date-input v-model="taskDateRange" label="Date range" multiple="range" clearable />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="addTaskDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="tonal" :disabled="!newTaskTitle" @click="handleAddTask">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
