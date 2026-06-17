<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { usersApi } from '@/api/modules'
import PaginationControls from '@/components/PaginationControls.vue'
import { useAuthStore } from '@/stores/auth'
import type { CurrentUser } from '@/types/api'

const auth = useAuthStore()

const users = ref<CurrentUser[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const pageOffset = ref(0)
const pageLimit = ref(25)
const pageTotal = ref(0)

const roleDialog = ref(false)
const roleUserId = ref<string | null>(null)
const selectedRole = ref<string>('developer')

const roleItems = ['superuser', 'administrator', 'developer']

function roleColor(role: string) {
  const map: Record<string, string> = { superuser: 'primary', administrator: 'secondary', developer: 'default' }
  return map[role] || 'default'
}

async function fetchUsers(offset = pageOffset.value, limit = pageLimit.value) {
  loading.value = true
  error.value = null
  try {
    const res = await usersApi.list({ offset, limit })
    users.value = res.data.data
    pageTotal.value = res.data.total
    pageOffset.value = offset
    pageLimit.value = limit
  } catch {
    error.value = 'Failed to load users.'
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: { offset: number; limit: number }) {
  fetchUsers(page.offset, page.limit)
}

onMounted(fetchUsers)

function openRoleDialog(user: CurrentUser) {
  roleUserId.value = user.id
  selectedRole.value = user.global_role
  roleDialog.value = true
}

async function handleRoleUpdate() {
  if (!roleUserId.value) return
  try {
    await usersApi.updateRole(roleUserId.value, selectedRole.value)
    const idx = users.value.findIndex((u) => u.id === roleUserId.value)
    if (idx !== -1) users.value[idx] = { ...users.value[idx], global_role: selectedRole.value as CurrentUser['global_role'] }
    roleDialog.value = false
  } catch {
    error.value = 'Failed to update role.'
  }
}

async function handleActiveChange(user: CurrentUser, value: boolean | null) {
  if (value === null) return
  try {
    await usersApi.updateActive(user.id, value)
    const idx = users.value.findIndex((u) => u.id === user.id)
    if (idx !== -1) users.value[idx] = { ...users.value[idx], is_active: value }
  } catch {
    error.value = 'Failed to update active status.'
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
        <h1 class="text-h5 mb-1">Users</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">Global RBAC roles and account state synced from OIDC.</p>
      </div>
    </div>

    <v-card border flat>
      <v-table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Active</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.display_name }}</td>
            <td>{{ user.email }}</td>
            <td>
              <v-chip
                v-if="auth.isAdmin"
                size="small"
                :color="roleColor(user.global_role)"
                variant="tonal"
                class="cursor-pointer"
                @click="openRoleDialog(user)"
              >
                {{ user.global_role }}
              </v-chip>
              <v-chip v-else size="small" :color="roleColor(user.global_role)" variant="tonal">
                {{ user.global_role }}
              </v-chip>
            </td>
            <td>
              <template v-if="auth.isAdmin">
                <v-switch
                  :model-value="user.is_active"
                  color="success"
                  hide-details
                  density="compact"
                  @update:model-value="(val: boolean | null) => handleActiveChange(user, val)"
                />
              </template>
              <template v-else>
                <v-chip size="small" :color="user.is_active ? 'success' : 'default'" variant="tonal">
                  {{ user.is_active ? 'active' : 'inactive' }}
                </v-chip>
              </template>
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

    <v-dialog v-model="roleDialog" max-width="400">
      <v-card title="Change Role">
        <v-card-text>
          <v-select
            v-model="selectedRole"
            :items="roleItems"
            label="Role"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="roleDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="tonal" @click="handleRoleUpdate">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
