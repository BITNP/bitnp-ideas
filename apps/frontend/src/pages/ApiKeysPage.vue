<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiKeysApi } from '@/api/modules'
import EmptyState from '@/components/EmptyState.vue'
import PaginationControls from '@/components/PaginationControls.vue'
import type { ApiKeyRead } from '@/types/api'

const keys = ref<ApiKeyRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const pageOffset = ref(0)
const pageLimit = ref(25)
const pageTotal = ref(0)
const query = ref('')
const selectedStatus = ref<string | null>(null)

const createDialog = ref(false)
const createName = ref('')
const createScopes = ref('')
const createdKeyDialog = ref(false)
const createdKeyId = ref('')
const createdSecret = ref('')
const copiedSecret = ref(false)

const revokeDialog = ref(false)
const revokeTarget = ref<ApiKeyRead | null>(null)

const filteredKeys = computed(() => {
  const normalizedQuery = query.value.trim().toLowerCase()
  return keys.value.filter((key) => {
    const matchesQuery = !normalizedQuery
      || key.name.toLowerCase().includes(normalizedQuery)
      || key.key_id.toLowerCase().includes(normalizedQuery)
      || key.scopes.some((scope) => scope.toLowerCase().includes(normalizedQuery))
    const matchesStatus = !selectedStatus.value || statusLabel(key) === selectedStatus.value
    return matchesQuery && matchesStatus
  })
})

const hasActiveFilters = computed(() => Boolean(query.value || selectedStatus.value))

async function fetchKeys(offset = pageOffset.value, limit = pageLimit.value) {
  loading.value = true
  error.value = null
  try {
    const res = await apiKeysApi.list({ offset, limit })
    keys.value = res.data.data
    pageTotal.value = res.data.total
    pageOffset.value = offset
    pageLimit.value = limit
  } catch {
    error.value = 'Failed to load API keys.'
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: { offset: number; limit: number }) {
  fetchKeys(page.offset, page.limit)
}

function clearFilters() {
  query.value = ''
  selectedStatus.value = null
}

onMounted(fetchKeys)

function openCreateDialog() {
  createName.value = ''
  createScopes.value = ''
  createDialog.value = true
}

async function handleCreate() {
  try {
    const res = await apiKeysApi.create({
      name: createName.value,
      scopes: createScopes.value ? createScopes.value.split(',').map((s) => s.trim()).filter(Boolean) : undefined,
    })
    keys.value.unshift(res.data.api_key)
    if (keys.value.length > pageLimit.value) {
      keys.value = keys.value.slice(0, pageLimit.value)
    }
    pageTotal.value += 1
    createDialog.value = false
    createdKeyId.value = res.data.api_key.key_id
    createdSecret.value = res.data.secret
    copiedSecret.value = false
    createdKeyDialog.value = true
    createName.value = ''
    createScopes.value = ''
  } catch {
    error.value = 'Failed to create API key.'
  }
}

async function copyCreatedSecret() {
  if (!createdSecret.value) return
  try {
    await navigator.clipboard.writeText(createdSecret.value)
    copiedSecret.value = true
  } catch {
    error.value = 'Failed to copy API key secret.'
  }
}

async function handleToggle(key: ApiKeyRead) {
  if (key.revoked_at) return
  try {
    const nextActive = !key.is_active
    await apiKeysApi.update(key.id, { is_active: nextActive })
    const idx = keys.value.findIndex((k) => k.id === key.id)
    if (idx !== -1) keys.value[idx] = { ...keys.value[idx], is_active: nextActive }
  } catch {
    error.value = 'Failed to update API key.'
  }
}

function statusLabel(key: ApiKeyRead) {
  if (key.revoked_at) return 'revoked'
  return key.is_active ? 'active' : 'inactive'
}

function statusColor(key: ApiKeyRead) {
  if (key.revoked_at) return 'error'
  return key.is_active ? 'success' : 'default'
}

function formatDate(value: string | null) {
  if (!value) return 'Never'
  return new Date(value).toLocaleString()
}

function shortKeyId(value: string) {
  if (value.length <= 24) return value
  return `${value.slice(0, 12)}...${value.slice(-8)}`
}

function entitySummary(key: ApiKeyRead) {
  if (key.allowed_entities.length === 0) return 'No entity access'
  return `Entities: ${key.allowed_entities.join(', ')}`
}

function handleRevoke(key: ApiKeyRead) {
  revokeTarget.value = key
  revokeDialog.value = true
}

async function handleConfirmRevoke() {
  const target = revokeTarget.value
  if (!target) return
  try {
    await apiKeysApi.revoke(target.id)
    await fetchKeys(pageOffset.value, pageLimit.value)
    revokeDialog.value = false
    revokeTarget.value = null
  } catch {
    error.value = 'Failed to revoke API key.'
  }
}
</script>

<template>
  <div class="page-shell">
    <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = null">
      {{ error }}
    </v-alert>

    <div class="toolbar-row mb-4">
      <div>
        <h1 class="text-h5 mb-1">API Keys</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">Create, pause, and permanently revoke external automation credentials.</p>
      </div>
      <v-btn color="primary" prepend-icon="$key" @click="openCreateDialog">Create key</v-btn>
    </div>

    <v-card border flat class="mb-4">
      <v-card-text class="d-flex flex-wrap ga-3 align-center">
        <v-text-field
          v-model="query"
          prepend-inner-icon="$search"
          label="Search keys"
          hide-details
        />
        <v-select
          v-model="selectedStatus"
          :items="['active', 'inactive', 'revoked']"
          clearable
          label="Status"
          hide-details
          max-width="220"
        />
        <v-btn
          variant="tonal"
          :disabled="!hasActiveFilters"
          @click="clearFilters"
        >
          Clear
        </v-btn>
      </v-card-text>
    </v-card>

    <v-card border flat>
      <v-table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Key ID</th>
            <th>Scopes</th>
            <th>Last used</th>
            <th>Created</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="key in filteredKeys" :key="key.id">
            <td>
              <div class="font-weight-medium">{{ key.name }}</div>
              <div class="text-caption text-medium-emphasis">{{ entitySummary(key) }}</div>
            </td>
            <td class="monospace-cell" :title="key.key_id"><code>{{ shortKeyId(key.key_id) }}</code></td>
            <td>
              <v-chip v-for="scope in key.scopes" :key="scope" size="small" color="primary" variant="tonal" class="mr-1 mb-1">
                {{ scope }}
              </v-chip>
            </td>
            <td class="nowrap-cell">{{ formatDate(key.last_used_at) }}</td>
            <td class="nowrap-cell">{{ formatDate(key.created_at) }}</td>
            <td>
              <v-chip size="small" :color="statusColor(key)" variant="tonal">
                {{ statusLabel(key) }}
              </v-chip>
            </td>
            <td>
              <v-btn
                size="small"
                variant="text"
                :color="key.is_active ? 'warning' : 'success'"
                :disabled="Boolean(key.revoked_at)"
                :prepend-icon="key.is_active ? '$block' : '$check'"
                :title="key.is_active ? 'Deactivate' : 'Activate'"
                :aria-label="key.is_active ? 'Deactivate API key' : 'Activate API key'"
                @click="handleToggle(key)"
              >
                {{ key.is_active ? 'Pause' : 'Activate' }}
              </v-btn>
              <v-btn
                size="small"
                variant="text"
                color="error"
                prepend-icon="$delete"
                :disabled="Boolean(key.revoked_at)"
                title="Revoke"
                aria-label="Revoke API key"
                @click="handleRevoke(key)"
              >
                Revoke
              </v-btn>
            </td>
          </tr>
          <tr v-if="!loading && filteredKeys.length === 0">
            <td colspan="7">
              <EmptyState
                icon="$key"
                :title="hasActiveFilters ? 'No keys match the filters' : 'No API keys yet'"
                :description="hasActiveFilters
                  ? 'Try a different name, key ID, scope, or status.'
                  : 'Create a key to let external automation submit or read idea intake data.'"
                :action-label="hasActiveFilters ? 'Clear filters' : 'Create key'"
                @action="hasActiveFilters ? clearFilters() : openCreateDialog()"
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

    <v-dialog v-model="createDialog" max-width="520">
      <v-card title="Create API key">
        <v-card-text>
          <v-text-field v-model="createName" label="Name" />
          <v-text-field v-model="createScopes" label="Scopes (comma-separated)" hint="e.g. ideas:read, ideas:write" persistent-hint />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="createDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="tonal" :disabled="!createName" @click="handleCreate">Create key</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="createdKeyDialog" max-width="640">
      <v-card title="API key created">
        <v-card-text>
          <v-alert type="warning" variant="tonal" class="mb-4">
            This signing secret is shown once. Copy it now; it cannot be recovered later.
          </v-alert>
          <v-text-field
            :model-value="createdKeyId"
            label="Key ID"
            readonly
          />
          <v-text-field
            :model-value="createdSecret"
            label="Signing secret"
            readonly
            append-inner-icon="$copy"
            @click:append-inner="copyCreatedSecret"
          />
          <v-alert v-if="copiedSecret" type="success" variant="tonal">
            Secret copied.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="createdKeyDialog = false">Done</v-btn>
          <v-btn color="primary" variant="tonal" @click="copyCreatedSecret">Copy secret</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="revokeDialog" max-width="480">
      <v-card title="Revoke API key">
        <v-card-text>
          <p class="mb-3">
            Revoke API key "{{ revokeTarget?.name }}"? This is permanent; the key cannot be reactivated or rotated.
          </p>
          <p class="text-body-2 text-medium-emphasis mb-0">
            The record remains visible for audit history. Use Pause instead when you only need a temporary stop.
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="revokeDialog = false">Cancel</v-btn>
          <v-btn color="error" variant="tonal" @click="handleConfirmRevoke">Revoke</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
