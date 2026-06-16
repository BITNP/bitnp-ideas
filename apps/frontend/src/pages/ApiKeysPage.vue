<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiKeysApi } from '@/api/modules'
import type { ApiKeyRead } from '@/types/api'

const keys = ref<ApiKeyRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const createDialog = ref(false)
const createName = ref('')
const createScopes = ref('')
const createAllowedEntities = ref('')

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    const res = await apiKeysApi.list()
    keys.value = res.data
  } catch {
    error.value = 'Failed to load API keys.'
  } finally {
    loading.value = false
  }
})

function openCreateDialog() {
  createName.value = ''
  createScopes.value = ''
  createAllowedEntities.value = ''
  createDialog.value = true
}

async function handleCreate() {
  try {
    const res = await apiKeysApi.create({
      name: createName.value,
      scopes: createScopes.value ? createScopes.value.split(',').map((s) => s.trim()).filter(Boolean) : undefined,
      allowed_entities: createAllowedEntities.value ? createAllowedEntities.value.split(',').map((s) => s.trim()).filter(Boolean) : undefined,
    })
    keys.value.unshift(res.data)
    createDialog.value = false
  } catch {
    error.value = 'Failed to create API key.'
  }
}

async function handleToggle(key: ApiKeyRead) {
  try {
    const res = await apiKeysApi.update(key.id, { is_active: !key.is_active })
    const idx = keys.value.findIndex((k) => k.id === key.id)
    if (idx !== -1) keys.value[idx] = res.data
  } catch {
    error.value = 'Failed to update API key.'
  }
}

async function handleDelete(key: ApiKeyRead) {
  if (!confirm(`Delete API key "${key.name}"? This action cannot be undone.`)) return
  try {
    await apiKeysApi.delete(key.id)
    keys.value = keys.value.filter((k) => k.id !== key.id)
  } catch {
    error.value = 'Failed to delete API key.'
  }
}
</script>

<template>
  <div class="page-shell">
    <v-progress-linear v-if="loading" indeterminate color="primary" />

    <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = null">
      {{ error }}
    </v-alert>

    <div class="toolbar-row mb-4">
      <div>
        <h1 class="text-h5 mb-1">API Keys</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">External automation is limited to idea intake scopes.</p>
      </div>
      <v-btn color="primary" prepend-icon="$key" @click="openCreateDialog">Create key</v-btn>
    </div>

    <v-card border flat>
      <v-table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Key ID</th>
            <th>Scopes</th>
            <th>Entities</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="key in keys" :key="key.id">
            <td>{{ key.name }}</td>
            <td><code>{{ key.key_id }}</code></td>
            <td>{{ key.scopes.join(', ') }}</td>
            <td>
              <v-chip v-for="entity in key.allowed_entities" :key="entity" size="small" color="primary" variant="tonal" class="mr-1">
                {{ entity }}
              </v-chip>
            </td>
            <td>
              <v-chip size="small" :color="key.is_active ? 'success' : 'default'" variant="tonal">
                {{ key.is_active ? 'active' : 'revoked' }}
              </v-chip>
            </td>
            <td>
              <v-btn
                icon
                size="small"
                variant="text"
                :color="key.is_active ? 'warning' : 'success'"
                :title="key.is_active ? 'Revoke' : 'Activate'"
                @click="handleToggle(key)"
              >
                <v-icon>{{ key.is_active ? '$block' : '$check' }}</v-icon>
              </v-btn>
              <v-btn
                icon
                size="small"
                variant="text"
                color="error"
                title="Delete"
                @click="handleDelete(key)"
              >
                <v-icon>$delete</v-icon>
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <v-dialog v-model="createDialog" max-width="520">
      <v-card title="Create API Key">
        <v-card-text>
          <v-text-field v-model="createName" label="Name" />
          <v-text-field v-model="createScopes" label="Scopes (comma-separated)" hint="e.g. ideas:read, ideas:write" persistent-hint />
          <v-text-field v-model="createAllowedEntities" label="Allowed Entities (comma-separated)" hint="e.g. idea, project" persistent-hint />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="createDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="tonal" :disabled="!createName" @click="handleCreate">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
