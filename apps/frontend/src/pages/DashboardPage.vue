<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'
import MetricTile from '@/components/MetricTile.vue'
import { activityApi, ideasApi, projectsApi, tasksApi } from '@/api/modules'
import type { ActivityRead, IdeaRead, ProjectRead, TaskRead } from '@/types/api'

const GanttBoard = defineAsyncComponent(() => import('@/components/GanttBoard.vue'))

interface ActivityDisplayItem {
  title: string
  subtitle: string
  icon: string
}

const ideas = ref<IdeaRead[]>([])
const projects = ref<ProjectRead[]>([])
const allTasks = ref<TaskRead[]>([])
const allActivities = ref<ActivityRead[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const activeIdeas = computed(() => ideas.value.filter((i) => i.status === 'active').length)
const activeProjects = computed(() => projects.value.filter((p) => p.status === 'active').length)
const openTasks = computed(() => allTasks.value.filter((t) => t.status !== 'done').length)
const totalIdeas = computed(() => ideas.value.length)

const projectNameMap = computed(() => {
  const map: Record<string, string> = {}
  for (const p of projects.value) {
    map[p.id] = p.name
  }
  return map
})

const recentActivities = computed(() =>
  [...allActivities.value]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5),
)

const activityItems = computed<ActivityDisplayItem[]>(() =>
  recentActivities.value.map((a) => {
    const actorName = a.actor?.name ?? 'Someone'
    const action = a.action_type.replace(/_/g, ' ')
    const entity = a.entity_type
    const projectName = projectNameMap.value[a.project_id] ?? 'Unknown'
    return {
      title: `${actorName} ${action} ${entity}`,
      subtitle: `${a.entity_type}.${a.action_type} · ${projectName}`,
      icon: '$activity',
    }
  }),
)

async function collectPages<T>(
  fetchPage: (params: { offset: number, limit: number }) => Promise<{ data: { data: T[], total: number } }>,
) {
  const limit = 100
  const items: T[] = []
  let offset = 0
  let total = 0

  do {
    const response = await fetchPage({ offset, limit })
    items.push(...response.data.data)
    total = response.data.total
    offset += limit
  } while (offset < total)

  return items
}

onMounted(async () => {
  loading.value = true
  error.value = null

  const [ideasResult, projectsResult] = await Promise.allSettled([
    collectPages<IdeaRead>((params) => ideasApi.list(params)),
    collectPages<ProjectRead>((params) => projectsApi.list(params)),
  ])

  if (ideasResult.status === 'fulfilled') {
    ideas.value = ideasResult.value
  }
  if (projectsResult.status === 'fulfilled') {
    projects.value = projectsResult.value
  }

  if (projects.value.length > 0) {
    const taskResults = await Promise.allSettled(
      projects.value.map((p) => collectPages<TaskRead>((params) => tasksApi.list(p.id, params))),
    )
    const activityResults = await Promise.allSettled(
      projects.value.map((p) => collectPages<ActivityRead>((params) => activityApi.list(p.id, params))),
    )

    const collectedTasks: TaskRead[] = []
    for (const result of taskResults) {
      if (result.status === 'fulfilled') {
        collectedTasks.push(...result.value)
      }
    }
    allTasks.value = collectedTasks

    const collectedActivities: ActivityRead[] = []
    for (const result of activityResults) {
      if (result.status === 'fulfilled') {
        collectedActivities.push(...result.value)
      }
    }
    allActivities.value = collectedActivities
  }

  if (ideasResult.status === 'rejected' && projectsResult.status === 'rejected') {
    error.value = 'Failed to load dashboard data. Please try again.'
  }

  loading.value = false
})
</script>

<template>
  <div class="page-shell">
    <v-alert
      v-if="error"
      type="error"
      :text="error"
      closable
      class="mb-4"
      @click:close="error = null"
    />

    <div class="toolbar-row mb-4">
      <div>
        <h1 class="text-h5 mb-1">Execution Overview</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">
          Idea intake, project delivery, and traceable execution.
        </p>
      </div>
      <v-btn color="primary" prepend-icon="$plus" to="/ideas">New idea</v-btn>
    </div>

    <div class="metric-grid mb-4">
      <MetricTile label="Active ideas" :value="activeIdeas" icon="$idea" tone="primary" />
      <MetricTile label="Active projects" :value="activeProjects" icon="$gantt" tone="secondary" />
      <MetricTile label="Open tasks" :value="openTasks" icon="$calendar" tone="accent" />
      <MetricTile label="Total ideas" :value="totalIdeas" icon="$idea" tone="success" />
    </div>

    <div class="content-grid">
      <GanttBoard :tasks="allTasks" compact readonly />

      <v-card border flat>
        <v-card-title>Recent activity</v-card-title>
        <v-list v-if="activityItems.length > 0" lines="two">
          <v-list-item
            v-for="item in activityItems"
            :key="item.title"
            :title="item.title"
            :subtitle="item.subtitle"
            :prepend-icon="item.icon"
          />
        </v-list>
        <v-card-text v-else class="text-medium-emphasis">
          No recent activity.
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>
