<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { projectsApi } from '@/api/modules'
import EmptyState from '@/components/EmptyState.vue'
import PaginationControls from '@/components/PaginationControls.vue'
import type { ProjectRead } from '@/types/api'

const router = useRouter()
const projects = ref<ProjectRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const pageOffset = ref(0)
const pageLimit = ref(25)
const pageTotal = ref(0)

const dialog = ref(false)
const form = ref({
  key: '',
  name: '',
  description: '',
  status: 'planning',
})
const submitting = ref(false)

async function fetchProjects(offset = pageOffset.value, limit = pageLimit.value) {
  loading.value = true
  error.value = null
  try {
    const res = await projectsApi.list({ offset, limit })
    projects.value = res.data.data
    pageTotal.value = res.data.total
    pageOffset.value = offset
    pageLimit.value = limit
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    error.value = err.response?.data?.detail ?? err.message ?? 'Failed to load projects'
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: { offset: number; limit: number }) {
  fetchProjects(page.offset, page.limit)
}

function openProject(project: ProjectRead) {
  router.push(`/projects/${project.id}`)
}

function statusColor(status: string) {
  if (status === 'active') return 'success'
  if (status === 'paused') return 'warning'
  if (status === 'completed') return 'primary'
  if (status === 'cancelled') return 'error'
  return 'secondary'
}

function memberSummary(project: ProjectRead) {
  if (project.members.length === 0) return 'No members'
  return project.members.map((m) => m.name).join(', ')
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString()
}

async function createProject() {
  submitting.value = true
  error.value = null
  try {
    await projectsApi.create(form.value)
    dialog.value = false
    form.value = { key: '', name: '', description: '', status: 'planning' }
    await fetchProjects(0, pageLimit.value)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    error.value = err.response?.data?.detail ?? err.message ?? 'Failed to create project'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchProjects()
})
</script>

<template>
  <div class="page-shell">
    <v-alert v-if="error" type="error" closable variant="tonal" class="mb-4" @click:close="error = null">
      {{ error }}
    </v-alert>

    <div class="toolbar-row mb-4">
      <div>
        <h1 class="text-h5 mb-1">Projects</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">Promoted idea containers with members, tasks, links, and activity.</p>
      </div>
      <v-btn color="primary" prepend-icon="$plus" @click="dialog = true">Create project</v-btn>
    </div>

    <v-card border flat>
      <v-table>
        <thead>
          <tr>
            <th>Key</th>
            <th>Name</th>
            <th>Status</th>
            <th>Progress</th>
            <th>Members</th>
            <th>Updated</th>
            <th class="text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="project in projects" :key="project.id" class="interactive-row" @click="openProject(project)">
            <td>
              <v-chip size="small" color="primary" variant="tonal">{{ project.key }}</v-chip>
            </td>
            <td>
              <div class="font-weight-medium">{{ project.name }}</div>
              <div class="text-caption text-medium-emphasis">{{ project.description || 'No description yet.' }}</div>
            </td>
            <td><v-chip size="small" :color="statusColor(project.status)" variant="tonal">{{ project.status }}</v-chip></td>
            <td>
              <v-progress-linear :model-value="project.progress" color="primary" height="8" rounded />
            </td>
            <td>{{ memberSummary(project) }}</td>
            <td class="nowrap-cell">{{ formatDate(project.updated_at) }}</td>
            <td class="text-right">
              <v-btn size="small" variant="text" color="primary" @click.stop="openProject(project)">Open</v-btn>
            </td>
          </tr>
          <tr v-if="!loading && projects.length === 0">
            <td colspan="7">
              <EmptyState
                icon="$gantt"
                title="No projects yet"
                description="Create a project when an idea is ready for members, tasks, links, and activity tracking."
                action-label="Create project"
                @action="dialog = true"
              />
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <PaginationControls
      :offset="pageOffset"
      :limit="pageLimit"
      :total="pageTotal"
      :loading="loading"
      @page-change="handlePageChange"
    />

    <v-dialog v-model="dialog" max-width="480">
      <v-card border flat>
        <v-card-title>Create project</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.key" label="Key" hint="Short identifier, e.g. EXEC" persistent-hint required />
          <v-text-field v-model="form.name" label="Name" required />
          <v-textarea v-model="form.description" label="Description" rows="3" />
          <v-select
            v-model="form.status"
            :items="['planning', 'active', 'paused', 'completed', 'cancelled']"
            label="Status"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="submitting" :disabled="!form.key || !form.name" @click="createProject">Create project</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
