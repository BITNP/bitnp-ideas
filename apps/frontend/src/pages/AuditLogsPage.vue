<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { VDateInput } from 'vuetify/components/VDateInput'

import { auditApi } from '@/api/modules'
import PaginationControls from '@/components/PaginationControls.vue'
import type { AuditLogRead } from '@/types/api'

const logs = ref<AuditLogRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const actionFilter = ref('')
const entityTypeFilter = ref<string | null>(null)
const entityIdFilter = ref('')
const actorUserFilter = ref('')
const actorApiKeyFilter = ref('')
const createdFromFilter = ref<Date | null>(null)
const createdToFilter = ref<Date | null>(null)
const selectedLog = ref<AuditLogRead | null>(null)
const pageOffset = ref(0)
const pageLimit = ref(25)
const pageTotal = ref(0)

const entityTypes = ['user', 'idea', 'idea_tag', 'project', 'task', 'task_dependency', 'api_key', 'external_link']

const activeFilterCount = computed(() => [
  actionFilter.value,
  entityTypeFilter.value,
  entityIdFilter.value,
  actorUserFilter.value,
  actorApiKeyFilter.value,
  createdFromFilter.value,
  createdToFilter.value,
].filter(Boolean).length)

const selectedPayload = computed(() => {
  if (!selectedLog.value) return ''
  return JSON.stringify({
    before: selectedLog.value.before,
    after: selectedLog.value.after,
    metadata: selectedLog.value.metadata,
  }, null, 2)
})

function dateToString(value: Date | null) {
  if (!value) return undefined
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

async function fetchLogs(offset = pageOffset.value, limit = pageLimit.value) {
  loading.value = true
  error.value = null
  try {
    const res = await auditApi.list({
      offset,
      limit,
      action: actionFilter.value || undefined,
      entity_type: entityTypeFilter.value || undefined,
      entity_id: entityIdFilter.value || undefined,
      actor_user_id: actorUserFilter.value || undefined,
      actor_api_key_id: actorApiKeyFilter.value || undefined,
      created_from: dateToString(createdFromFilter.value),
      created_to: dateToString(createdToFilter.value),
    })
    logs.value = res.data.data
    pageTotal.value = res.data.total
    pageOffset.value = offset
    pageLimit.value = limit
  } catch {
    error.value = 'Failed to load audit logs.'
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  fetchLogs(0, pageLimit.value)
}

function clearFilters() {
  actionFilter.value = ''
  entityTypeFilter.value = null
  entityIdFilter.value = ''
  actorUserFilter.value = ''
  actorApiKeyFilter.value = ''
  createdFromFilter.value = null
  createdToFilter.value = null
  fetchLogs(0, pageLimit.value)
}

function handlePageChange(page: { offset: number; limit: number }) {
  fetchLogs(page.offset, page.limit)
}

function openLog(log: AuditLogRead) {
  selectedLog.value = log
}

onMounted(fetchLogs)
</script>

<template>
  <div class="page-shell">
    <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = null">
      {{ error }}
    </v-alert>

    <div class="toolbar-row mb-4">
      <div>
        <h1 class="text-h5 mb-1">Audit Logs</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">
          System-level immutable event history for superuser review.
        </p>
      </div>
      <v-btn
        color="primary"
        variant="tonal"
        prepend-icon="$activity"
        :loading="loading"
        @click="fetchLogs(0, pageLimit)"
      >
        Refresh
      </v-btn>
    </div>

    <v-card border flat class="mb-4">
      <v-card-text>
        <div class="audit-filter-grid">
          <v-text-field
            v-model="actionFilter"
            prepend-inner-icon="$search"
            label="Action"
            hide-details
          />
          <v-select
            v-model="entityTypeFilter"
            :items="entityTypes"
            clearable
            label="Entity type"
            hide-details
          />
          <v-text-field
            v-model="entityIdFilter"
            label="Entity ID"
            hide-details
          />
          <v-text-field
            v-model="actorUserFilter"
            label="Actor user ID"
            hide-details
          />
          <v-text-field
            v-model="actorApiKeyFilter"
            label="Actor API key ID"
            hide-details
          />
          <v-date-input
            v-model="createdFromFilter"
            label="Created from"
            clearable
            hide-details
          />
          <v-date-input
            v-model="createdToFilter"
            label="Created to"
            clearable
            hide-details
          />
          <div class="filter-actions">
            <v-btn color="primary" prepend-icon="$search" :loading="loading" @click="applyFilters">
              Apply
            </v-btn>
            <v-btn variant="tonal" :disabled="activeFilterCount === 0 || loading" @click="clearFilters">
              Clear
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <v-card border flat>
      <v-table>
        <thead>
          <tr>
            <th>Action</th>
            <th>Entity</th>
            <th>Actor</th>
            <th>Created</th>
            <th class="text-right">Details</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id">
            <td>
              <v-chip size="small" color="primary" variant="tonal">{{ log.action }}</v-chip>
            </td>
            <td>
              <div class="font-weight-medium">{{ log.entity_type }}</div>
              <div class="text-caption text-medium-emphasis">{{ log.entity_id ?? 'system' }}</div>
            </td>
            <td>
              <span v-if="log.actor_user_id">{{ log.actor_user_id }}</span>
              <v-chip v-else-if="log.actor_api_key_id" size="small" color="secondary" variant="tonal">
                API Key
              </v-chip>
              <span v-else class="text-medium-emphasis">System</span>
            </td>
            <td>{{ new Date(log.created_at).toLocaleString() }}</td>
            <td class="text-right">
              <v-btn size="small" variant="text" color="primary" @click="openLog(log)">View</v-btn>
            </td>
          </tr>
          <tr v-if="!loading && logs.length === 0">
            <td colspan="5">
              <div class="text-center text-medium-emphasis py-6">No audit logs match the filters.</div>
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

    <v-dialog :model-value="!!selectedLog" max-width="720" @update:model-value="selectedLog = null">
      <v-card v-if="selectedLog">
        <v-card-title class="d-flex align-center">
          <span>{{ selectedLog.action }}</span>
          <v-spacer />
          <v-btn icon="$close" variant="text" @click="selectedLog = null" />
        </v-card-title>
        <v-card-text>
          <div class="d-flex flex-wrap ga-2 mb-4">
            <v-chip size="small" color="primary" variant="tonal">{{ selectedLog.entity_type }}</v-chip>
            <v-chip size="small" variant="tonal">{{ selectedLog.entity_id ?? 'system' }}</v-chip>
            <v-chip size="small" variant="tonal">{{ new Date(selectedLog.created_at).toLocaleString() }}</v-chip>
          </div>
          <v-textarea
            :model-value="selectedPayload"
            label="Payload"
            rows="14"
            readonly
            auto-grow
          />
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.audit-filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  align-items: start;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  min-height: 40px;
}
</style>
