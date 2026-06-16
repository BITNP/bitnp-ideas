<script setup lang="ts">
import { useWorkspaceStore } from '@/stores/workspace'

const store = useWorkspaceStore()
</script>

<template>
  <div class="page-shell">
    <div class="toolbar-row mb-4">
      <div>
        <h1 class="text-h5 mb-1">Projects</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">Promoted idea containers with members, tasks, links, and activity.</p>
      </div>
      <v-btn color="primary" prepend-icon="$plus">Create project</v-btn>
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
          <tr v-for="project in store.projects" :key="project.id">
            <td>
              <router-link :to="`/projects/${project.id}`">{{ project.key }}</router-link>
            </td>
            <td>{{ project.name }}</td>
            <td><v-chip size="small" color="secondary" variant="tonal">{{ project.status }}</v-chip></td>
            <td>
              <v-progress-linear :model-value="project.progress" color="primary" height="8" rounded />
            </td>
            <td>{{ project.members.join(', ') }}</td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </div>
</template>

