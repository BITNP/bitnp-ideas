<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { VDateInput } from 'vuetify/components/VDateInput'

import EmptyState from '@/components/EmptyState.vue'
import MetricTile from '@/components/MetricTile.vue'
import PaginationControls from '@/components/PaginationControls.vue'
import { projectsApi, tasksApi, ganttApi, activityApi, linksApi, usersApi, ideasApi } from '@/api/modules'
import { useAuthStore } from '@/stores/auth'
import type {
  ProjectRead,
  TaskRead,
  GanttRead,
  ActivityRead,
  IdeaRead,
  ExternalLinkRead,
  CurrentUser,
} from '@/types/api'

const route = useRoute()
const auth = useAuthStore()
const projectId = route.params.id as string
const GanttBoard = defineAsyncComponent(() => import('@/components/GanttBoard.vue'))

const tab = ref(route.name === 'project-gantt' ? 'gantt' : route.name === 'project-activity' ? 'activity' : 'overview')

const project = ref<ProjectRead | null>(null)
const tasks = ref<TaskRead[]>([])
const ganttData = ref<GanttRead | null>(null)
const activities = ref<ActivityRead[]>([])
const projectIdeas = ref<IdeaRead[]>([])
const links = ref<ExternalLinkRead[]>([])
const users = ref<CurrentUser[]>([])
const ideaOptions = ref<IdeaRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const taskOffset = ref(0)
const taskLimit = ref(25)
const taskTotal = ref(0)
const openTaskTotal = ref(0)
const ideaOffset = ref(0)
const ideaLimit = ref(25)
const ideaTotal = ref(0)
const linkOffset = ref(0)
const linkLimit = ref(25)
const linkTotal = ref(0)
const activityOffset = ref(0)
const activityLimit = ref(25)
const activityTotal = ref(0)

const openTaskCount = computed(() => openTaskTotal.value)
const memberIds = computed(() => new Set(project.value?.members.map((member) => member.id) ?? []))
const availableUsers = computed(() => users.value.filter((user) => !memberIds.value.has(user.id)))
const linkedIdeaIds = computed(() => new Set(projectIdeas.value.map((idea) => idea.id)))
const availableIdeas = computed(() => ideaOptions.value.filter((idea) => !linkedIdeaIds.value.has(idea.id)))
const canManageProject = computed(() => auth.isAdmin)
const canEditProjectWork = computed(() => {
  if (!auth.user) return false
  return canManageProject.value || memberIds.value.has(auth.user.id)
})

const addTaskDialog = ref(false)
const newTaskTitle = ref('')
const newTaskDescription = ref('')
const newTaskAssignee = ref<string | null>(null)
const taskDateRange = ref<Date[]>([])

const memberDialog = ref(false)
const selectedMemberId = ref<string | null>(null)

const ideaDialog = ref(false)
const selectedIdeaId = ref<string | null>(null)
const selectedIdeaRelation = ref('related')

const linkDialog = ref(false)
const linkUrl = ref('')
const linkTitle = ref('')
const linkDescription = ref('')
const linkType = ref('website')

const taskDrawer = ref(false)
const selectedTask = ref<TaskRead | null>(null)
const taskTitle = ref('')
const taskDescription = ref('')
const taskStatus = ref('todo')
const taskAssigneeId = ref<string | null>(null)
const taskStartDate = ref<Date | null>(null)
const taskEndDate = ref<Date | null>(null)
const taskProgress = ref(0)

const settingsName = ref('')
const settingsStatus = ref('')
const settingsDescription = ref('')

const taskStatuses = ['todo', 'in_progress', 'blocked', 'review', 'done', 'cancelled']
const ideaRelations = ['related', 'origin', 'inspired_by']
const linkTypes = ['website', 'github_repo', 'doc', 'other']

function dateFromString(value: string | null) {
  return value ? new Date(`${value}T00:00:00`) : null
}

function dateToString(value: Date | null) {
  if (!value) return null
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function dateRangeToString(value: Date | string | null | undefined) {
  if (!value) return undefined
  if (value instanceof Date) return dateToString(value) ?? undefined
  return value.slice(0, 10)
}

function requireProjectManagement() {
  if (canManageProject.value) return true
  error.value = 'You do not have permission to manage this project.'
  return false
}

function requireProjectWorkEdit() {
  if (canEditProjectWork.value) return true
  error.value = 'You do not have permission to edit project work.'
  return false
}

function applyProject(value: ProjectRead) {
  project.value = value
  settingsName.value = value.name
  settingsStatus.value = value.status
  settingsDescription.value = value.description ?? ''
}

async function fetchProject() {
  const res = await projectsApi.get(projectId)
  applyProject(res.data)
}

function countOpenTasks(values: TaskRead[]) {
  return values.filter((task) => task.status !== 'done').length
}

async function fetchReferenceData() {
  const [usersRes, ideasRes] = await Promise.all([
    usersApi.list({ offset: 0, limit: 100 }),
    ideasApi.list({ offset: 0, limit: 100 }),
  ])
  users.value = usersRes.data.data
  ideaOptions.value = ideasRes.data.data
}

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    await Promise.all([fetchProject(), fetchReferenceData()])
  } catch {
    error.value = 'Failed to load project.'
    loading.value = false
    return
  }

  try {
    const res = await tasksApi.list(projectId, { offset: taskOffset.value, limit: taskLimit.value })
    tasks.value = res.data.data
    taskTotal.value = res.data.total
    await refreshOpenTaskTotal(res.data.data, res.data.total, taskLimit.value)
  } catch {
    // tasks are optional for overview display
  }

  await fetchIdeas(0, ideaLimit.value)

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
    fetchTasks()
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

async function fetchTasks(offset = taskOffset.value, limit = taskLimit.value) {
  try {
    const res = await tasksApi.list(projectId, { offset, limit })
    tasks.value = res.data.data
    taskTotal.value = res.data.total
    taskOffset.value = offset
    taskLimit.value = limit
    if (offset === 0) {
      await refreshOpenTaskTotal(res.data.data, res.data.total, limit)
    }
  } catch { /* empty */ }
}

async function refreshOpenTaskTotal(firstPage: TaskRead[], total: number, firstPageLimit: number) {
  let offset = firstPageLimit
  let openCount = countOpenTasks(firstPage)

  while (offset < total) {
    const res = await tasksApi.list(projectId, { offset, limit: 100 })
    openCount += countOpenTasks(res.data.data)
    offset += 100
  }

  openTaskTotal.value = openCount
}

async function fetchActivities(offset = activityOffset.value, limit = activityLimit.value) {
  try {
    const res = await activityApi.list(projectId, { offset, limit })
    activities.value = res.data.data
    activityTotal.value = res.data.total
    activityOffset.value = offset
    activityLimit.value = limit
  } catch { /* empty */ }
}

async function fetchIdeas(offset = ideaOffset.value, limit = ideaLimit.value) {
  try {
    const res = await projectsApi.listIdeas(projectId, { offset, limit })
    projectIdeas.value = res.data.data
    ideaTotal.value = res.data.total
    ideaOffset.value = offset
    ideaLimit.value = limit
  } catch { /* empty */ }
}

async function fetchLinks(offset = linkOffset.value, limit = linkLimit.value) {
  try {
    const res = await linksApi.list('project', projectId, { offset, limit })
    links.value = res.data.data
    linkTotal.value = res.data.total
    linkOffset.value = offset
    linkLimit.value = limit
  } catch { /* empty */ }
}

async function fetchGantt() {
  try {
    const res = await ganttApi.get(projectId)
    ganttData.value = res.data
  } catch {
    ganttData.value = null
  }
}

function openTask(task: TaskRead) {
  selectedTask.value = task
  taskTitle.value = task.title
  taskDescription.value = task.description ?? ''
  taskStatus.value = task.status
  taskAssigneeId.value = task.assignee?.id ?? null
  taskStartDate.value = dateFromString(task.start_date)
  taskEndDate.value = dateFromString(task.end_date)
  taskProgress.value = task.progress
  taskDrawer.value = true
}

async function handleAddTask() {
  if (!requireProjectWorkEdit()) return
  if (!newTaskTitle.value) return
  try {
    const res = await tasksApi.create(projectId, {
      title: newTaskTitle.value,
      description: newTaskDescription.value || undefined,
      assignee_id: newTaskAssignee.value || undefined,
      start_date: dateRangeToString(taskDateRange.value[0]) || undefined,
      end_date: dateRangeToString(taskDateRange.value[1]) || undefined,
    })
    tasks.value.push(res.data)
    addTaskDialog.value = false
    newTaskTitle.value = ''
    newTaskDescription.value = ''
    newTaskAssignee.value = null
    taskDateRange.value = []
    await fetchTasks(0, taskLimit.value)
    if (ganttData.value) {
      fetchGantt()
    }
  } catch {
    error.value = 'Failed to create task.'
  }
}

async function handleSaveTask() {
  if (!requireProjectWorkEdit()) return
  if (!selectedTask.value || !taskTitle.value) return
  try {
    const res = await tasksApi.update(selectedTask.value.id, {
      title: taskTitle.value,
      description: taskDescription.value || undefined,
      status: taskStatus.value,
      assignee_id: taskAssigneeId.value,
      start_date: dateToString(taskStartDate.value),
      end_date: dateToString(taskEndDate.value),
      progress: taskProgress.value,
      version: selectedTask.value.version,
    })
    const idx = tasks.value.findIndex((task) => task.id === res.data.id)
    if (idx !== -1) tasks.value[idx] = res.data
    selectedTask.value = res.data
    openTask(res.data)
    if (ganttData.value) fetchGantt()
    fetchActivities(activityOffset.value, activityLimit.value)
  } catch {
    error.value = 'Failed to update task.'
  }
}

async function handleArchiveTask() {
  if (!requireProjectWorkEdit()) return
  if (!selectedTask.value) return
  try {
    await tasksApi.delete(selectedTask.value.id)
    taskDrawer.value = false
    selectedTask.value = null
    await fetchTasks(taskOffset.value, taskLimit.value)
    if (ganttData.value) fetchGantt()
    fetchActivities(activityOffset.value, activityLimit.value)
  } catch {
    error.value = 'Failed to archive task.'
  }
}

async function handleAddMember() {
  if (!requireProjectManagement()) return
  if (!selectedMemberId.value) return
  try {
    await projectsApi.addMember(projectId, selectedMemberId.value)
    selectedMemberId.value = null
    memberDialog.value = false
    await fetchProject()
    fetchActivities(activityOffset.value, activityLimit.value)
  } catch {
    error.value = 'Failed to add project member.'
  }
}

async function handleRemoveMember(userId: string) {
  if (!requireProjectManagement()) return
  try {
    await projectsApi.removeMember(projectId, userId)
    await fetchProject()
    fetchActivities(activityOffset.value, activityLimit.value)
  } catch {
    error.value = 'Failed to remove project member.'
  }
}

async function handleLinkIdea() {
  if (!requireProjectManagement()) return
  if (!selectedIdeaId.value) return
  try {
    await projectsApi.addIdea(projectId, selectedIdeaId.value, selectedIdeaRelation.value)
    selectedIdeaId.value = null
    selectedIdeaRelation.value = 'related'
    ideaDialog.value = false
    await fetchIdeas(0, ideaLimit.value)
    fetchActivities(activityOffset.value, activityLimit.value)
  } catch {
    error.value = 'Failed to link idea.'
  }
}

async function handleUnlinkIdea(ideaId: string) {
  if (!requireProjectManagement()) return
  try {
    await projectsApi.removeIdea(projectId, ideaId)
    await fetchIdeas(ideaOffset.value, ideaLimit.value)
    fetchActivities(activityOffset.value, activityLimit.value)
  } catch {
    error.value = 'Failed to unlink idea.'
  }
}

async function handleCreateLink() {
  if (!requireProjectWorkEdit()) return
  if (!linkUrl.value) return
  try {
    await linksApi.create('project', projectId, {
      url: linkUrl.value,
      title: linkTitle.value || undefined,
      description: linkDescription.value || undefined,
      link_type: linkType.value,
    })
    linkDialog.value = false
    linkUrl.value = ''
    linkTitle.value = ''
    linkDescription.value = ''
    linkType.value = 'website'
    await fetchLinks(0, linkLimit.value)
  } catch {
    error.value = 'Failed to create link.'
  }
}

async function handleDeleteLink(linkId: string) {
  if (!requireProjectWorkEdit()) return
  try {
    await linksApi.delete(linkId)
    await fetchLinks(linkOffset.value, linkLimit.value)
  } catch {
    error.value = 'Failed to delete link.'
  }
}

async function handleSaveSettings() {
  if (!requireProjectManagement()) return
  if (!project.value) return
  try {
    const res = await projectsApi.update(projectId, {
      name: settingsName.value,
      status: settingsStatus.value,
      description: settingsDescription.value,
    })
    applyProject(res.data)
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
        <div class="d-flex flex-wrap ga-2 justify-end">
          <v-btn
            v-if="canEditProjectWork"
            color="primary"
            prepend-icon="$plus"
            @click="addTaskDialog = true"
          >
            Add task
          </v-btn>
          <v-btn
            v-if="canManageProject"
            variant="tonal"
            prepend-icon="$users"
            @click="memberDialog = true"
          >
            Add member
          </v-btn>
        </div>
      </div>

      <v-tabs v-model="tab" class="mb-4">
        <v-tab value="overview">Overview</v-tab>
        <v-tab value="tasks">Tasks</v-tab>
        <v-tab value="gantt">Gantt</v-tab>
        <v-tab value="ideas">Ideas</v-tab>
        <v-tab value="links">Links</v-tab>
        <v-tab value="activity">Activity</v-tab>
        <v-tab v-if="canManageProject" value="settings">Settings</v-tab>
      </v-tabs>

      <v-window v-model="tab">
        <v-window-item value="overview">
          <div class="metric-grid mb-4">
            <MetricTile label="Progress" :value="`${project.progress}%`" icon="$check" tone="success" />
            <MetricTile label="Members" :value="project.members.length" icon="$users" tone="secondary" />
            <MetricTile label="Open tasks" :value="openTaskCount" icon="$calendar" tone="primary" />
            <MetricTile label="Linked ideas" :value="ideaTotal" icon="$idea" tone="accent" />
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
                  @click="openTask(task)"
                />
              </v-list>
              <v-card-text v-else class="text-medium-emphasis">No tasks yet.</v-card-text>
            </v-card>
            <v-card border flat>
              <v-card-title class="d-flex align-center">
                <span>Members</span>
                <v-spacer />
                <v-btn
                  v-if="canManageProject"
                  icon="$plus"
                  variant="text"
                  size="small"
                  @click="memberDialog = true"
                />
              </v-card-title>
              <v-list v-if="project.members.length">
                <v-list-item
                  v-for="member in project.members"
                  :key="member.id"
                  :title="member.name"
                  prepend-icon="$account"
                >
                  <template v-if="canManageProject" #append>
                    <v-btn
                      icon="$delete"
                      variant="text"
                      size="small"
                      @click.stop="handleRemoveMember(member.id)"
                    />
                  </template>
                </v-list-item>
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
                <tr v-for="task in tasks" :key="task.id" class="table-row-action" @click="openTask(task)">
                  <td>{{ task.title }}</td>
                  <td>{{ task.assignee?.name ?? '—' }}</td>
                  <td><v-chip size="small" color="primary" variant="tonal">{{ task.status }}</v-chip></td>
                  <td><v-slider :model-value="task.progress" hide-details density="compact" readonly /></td>
                </tr>
              </tbody>
            </v-table>
          </v-card>
          <v-card v-else border flat>
            <v-card-text class="text-medium-emphasis">No tasks yet.</v-card-text>
          </v-card>
          <PaginationControls
            :offset="taskOffset"
            :limit="taskLimit"
            :total="taskTotal"
            @page-change="(page) => fetchTasks(page.offset, page.limit)"
          />
        </v-window-item>

        <v-window-item value="gantt">
          <GanttBoard
            v-if="ganttData"
            :tasks="ganttData.tasks ?? []"
            :dependencies="ganttData.dependencies ?? []"
            :project-id="projectId"
            :readonly="!canEditProjectWork"
            :show-create-task-action="canEditProjectWork"
            @refresh="fetchGantt"
            @error="handleGanttError"
            @create-task="addTaskDialog = true"
          />
          <v-card v-else border flat>
            <EmptyState
              icon="$gantt"
              title="Plan data is unavailable"
              description="Refresh the project plan or add a task to start rebuilding the timeline."
              :action-label="canEditProjectWork ? 'Add task' : undefined"
              @action="addTaskDialog = true"
            />
          </v-card>
        </v-window-item>

        <v-window-item value="ideas">
          <div v-if="canManageProject" class="d-flex justify-end mb-3">
            <v-btn color="primary" variant="tonal" prepend-icon="$plus" @click="ideaDialog = true">Link idea</v-btn>
          </div>
          <v-card v-if="projectIdeas.length" border flat>
            <v-list lines="two">
              <v-list-item
                v-for="idea in projectIdeas"
                :key="idea.id"
                :title="idea.title"
                :subtitle="idea.status"
                prepend-icon="$idea"
              >
                <template v-if="canManageProject" #append>
                  <v-btn
                    icon="$delete"
                    variant="text"
                    size="small"
                    @click.stop="handleUnlinkIdea(idea.id)"
                  />
                </template>
              </v-list-item>
            </v-list>
          </v-card>
          <v-card v-else border flat>
            <v-card-text class="text-medium-emphasis">No linked ideas yet.</v-card-text>
          </v-card>
          <PaginationControls
            :offset="ideaOffset"
            :limit="ideaLimit"
            :total="ideaTotal"
            @page-change="(page) => fetchIdeas(page.offset, page.limit)"
          />
        </v-window-item>

        <v-window-item value="links">
          <div v-if="canEditProjectWork" class="d-flex justify-end mb-3">
            <v-btn color="primary" variant="tonal" prepend-icon="$plus" @click="linkDialog = true">Add link</v-btn>
          </div>
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
              >
                <template v-if="canEditProjectWork" #append>
                  <v-btn
                    icon="$delete"
                    variant="text"
                    size="small"
                    @click.prevent.stop="handleDeleteLink(link.id)"
                  />
                </template>
              </v-list-item>
            </v-list>
          </v-card>
          <v-card v-else border flat>
            <v-card-text class="text-medium-emphasis">No links yet.</v-card-text>
          </v-card>
          <PaginationControls
            :offset="linkOffset"
            :limit="linkLimit"
            :total="linkTotal"
            @page-change="(page) => fetchLinks(page.offset, page.limit)"
          />
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
          <PaginationControls
            :offset="activityOffset"
            :limit="activityLimit"
            :total="activityTotal"
            @page-change="(page) => fetchActivities(page.offset, page.limit)"
          />
        </v-window-item>

        <v-window-item v-if="canManageProject" value="settings">
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

    <v-dialog v-if="canEditProjectWork" v-model="addTaskDialog" max-width="520">
      <v-card title="Add Task">
        <v-card-text>
          <v-text-field v-model="newTaskTitle" label="Title" />
          <v-textarea v-model="newTaskDescription" label="Description" rows="3" />
          <v-autocomplete
            v-model="newTaskAssignee"
            :items="project?.members ?? []"
            item-title="name"
            item-value="id"
            label="Assignee"
            clearable
          />
          <v-date-input v-model="taskDateRange" label="Date range" multiple="range" clearable />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="addTaskDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="tonal" :disabled="!newTaskTitle" @click="handleAddTask">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-if="canManageProject" v-model="memberDialog" max-width="480">
      <v-card title="Add Member">
        <v-card-text>
          <v-autocomplete
            v-model="selectedMemberId"
            :items="availableUsers"
            item-title="display_name"
            item-value="id"
            label="User"
            clearable
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="memberDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="tonal" :disabled="!selectedMemberId" @click="handleAddMember">Add</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-if="canManageProject" v-model="ideaDialog" max-width="520">
      <v-card title="Link Idea">
        <v-card-text>
          <v-autocomplete
            v-model="selectedIdeaId"
            :items="availableIdeas"
            item-title="title"
            item-value="id"
            label="Idea"
            clearable
          />
          <v-select v-model="selectedIdeaRelation" :items="ideaRelations" label="Relation" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="ideaDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="tonal" :disabled="!selectedIdeaId" @click="handleLinkIdea">Link</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-if="canEditProjectWork" v-model="linkDialog" max-width="560">
      <v-card title="Add Link">
        <v-card-text>
          <v-text-field v-model="linkUrl" label="URL" prepend-inner-icon="$link" />
          <v-text-field v-model="linkTitle" label="Title" />
          <v-textarea v-model="linkDescription" label="Description" rows="3" />
          <v-select v-model="linkType" :items="linkTypes" label="Type" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="linkDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="tonal" :disabled="!linkUrl" @click="handleCreateLink">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-navigation-drawer v-model="taskDrawer" temporary location="right" width="460">
      <template v-if="selectedTask">
        <v-toolbar flat>
          <v-toolbar-title>Task detail</v-toolbar-title>
          <v-btn v-if="canEditProjectWork" icon="$delete" variant="text" @click="handleArchiveTask" />
          <v-btn icon="$close" variant="text" @click="taskDrawer = false" />
        </v-toolbar>
        <div class="pa-4">
          <v-text-field v-model="taskTitle" label="Title" :readonly="!canEditProjectWork" />
          <v-textarea v-model="taskDescription" label="Description" rows="3" :readonly="!canEditProjectWork" />
          <v-select v-model="taskStatus" :items="taskStatuses" label="Status" :readonly="!canEditProjectWork" />
          <v-autocomplete
            v-model="taskAssigneeId"
            :items="project?.members ?? []"
            item-title="name"
            item-value="id"
            label="Assignee"
            clearable
            :readonly="!canEditProjectWork"
          />
          <div class="d-flex ga-3">
            <v-date-input v-model="taskStartDate" label="Start" clearable :readonly="!canEditProjectWork" />
            <v-date-input v-model="taskEndDate" label="End" clearable :readonly="!canEditProjectWork" />
          </div>
          <v-slider
            v-model="taskProgress"
            label="Progress"
            min="0"
            max="100"
            step="5"
            thumb-label
            :readonly="!canEditProjectWork"
          />
          <v-btn
            v-if="canEditProjectWork"
            block
            color="primary"
            variant="tonal"
            :disabled="!taskTitle"
            @click="handleSaveTask"
          >
            Save task
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>
  </div>
</template>

<style scoped>
.table-row-action {
  cursor: pointer;
}
</style>
