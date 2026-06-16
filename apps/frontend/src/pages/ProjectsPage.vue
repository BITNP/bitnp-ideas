<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { projectsApi } from '@/api/modules'
import type { ProjectRead } from '@/types/api'

const projects = ref<ProjectRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const dialog = ref(false)
const form = ref({
  key: '',
  name: '',
  description: '',
  status: 'planning',
})
const submitting = ref(false)

async function fetchProjects() {
  loading.value = true
  error.value = null
  try {
    const res = await projectsApi.list()
    projects.value = res.data
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } }; message?: string }
    error.value = err.response?.data?.detail ?? err.message ?? 'Failed to load projects'
  } finally {
    loading.value = false
  }
}

async function createProject() {
  submitting.value = true
  error.value = null
  try {
    await projectsApi.create(form.value)
    dialog.value = false
    form.value = { key: '', name: '', description: '', status: 'planning' }
    await fetchProjects()
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
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-0" />

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
          </tr>
        </thead>
        <tbody>
          <tr v-for="project in projects" :key="project.id">
            <td>
              <v-btn variant="plain" density="compact" class="pa-0 text-none" :to="`/projects/${project.id}`">{{ project.key }}</v-btn>
            </td>
            <td>{{ project.name }}</td>
            <td><v-chip size="small" color="secondary" variant="tonal">{{ project.status }}</v-chip></td>
            <td>
              <v-progress-linear :model-value="project.progress" color="primary" height="8" rounded />
            </td>
            <td>{{ project.members.map(m => m.name).join(', ') }}</td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <v-dialog v-model="dialog" max-width="480">
      <v-card border flat>
        <v-card-title>Create project</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.key" label="Key" required />
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
          <v-btn color="primary" :loading="submitting" @click="createProject">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
