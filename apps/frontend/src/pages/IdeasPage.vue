<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { ideasApi, tagsApi } from '@/api/modules'
import EmptyState from '@/components/EmptyState.vue'
import PaginationControls from '@/components/PaginationControls.vue'
import type { IdeaRead, TagRead } from '@/types/api'

const ideas = ref<IdeaRead[]>([])
const tags = ref<TagRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const pageOffset = ref(0)
const pageLimit = ref(25)
const pageTotal = ref(0)

const query = ref('')
const selectedStatus = ref<string | null>(null)
const selectedTag = ref<string | null>(null)
const drawer = ref(false)
const activeIdeaId = ref<string | null>(null)

const createDialog = ref(false)
const createTitle = ref('')
const createDescription = ref('')
const createPriority = ref('medium')
const createTagIds = ref<string[]>([])

const filteredIdeas = computed(() => ideas.value)

const activeIdea = computed(() => ideas.value.find((idea) => idea.id === activeIdeaId.value))
const hasActiveFilters = computed(() => Boolean(query.value || selectedStatus.value || selectedTag.value))

async function fetchIdeas(offset = pageOffset.value, limit = pageLimit.value) {
  loading.value = true
  error.value = null
  try {
    const res = await ideasApi.list({
      offset,
      limit,
      status: selectedStatus.value ?? undefined,
      tag: selectedTag.value ?? undefined,
      search: query.value || undefined,
    })
    ideas.value = res.data.data
    pageTotal.value = res.data.total
    pageOffset.value = offset
    pageLimit.value = limit
  } catch {
    error.value = 'Failed to load ideas. Please try again.'
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: { offset: number; limit: number }) {
  fetchIdeas(page.offset, page.limit)
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString()
}

function clearFilters() {
  query.value = ''
  selectedStatus.value = null
  selectedTag.value = null
  fetchIdeas(0, pageLimit.value)
}

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    const [ideasRes, tagsRes] = await Promise.all([
      ideasApi.list({ offset: pageOffset.value, limit: pageLimit.value }),
      tagsApi.list({ offset: 0, limit: 100 }),
    ])
    ideas.value = ideasRes.data.data
    pageTotal.value = ideasRes.data.total
    tags.value = tagsRes.data.data
  } catch {
    error.value = 'Failed to load ideas. Please try again.'
  } finally {
    loading.value = false
  }
})

watch([query, selectedStatus, selectedTag], () => {
  fetchIdeas(0, pageLimit.value)
})

function openIdea(id: string) {
  activeIdeaId.value = id
  drawer.value = true
}

async function handleStatusChange(id: string, status: string) {
  try {
    await ideasApi.updateStatus(id, { status })
    const res = await ideasApi.get(id)
    const idx = ideas.value.findIndex((i) => i.id === id)
    if (idx !== -1) ideas.value[idx] = res.data
  } catch {
    error.value = 'Failed to update status. In progress and completed ideas require a linked project or URL.'
  }
}

async function handleDelete(id: string) {
  try {
    await ideasApi.delete(id)
    ideas.value = ideas.value.filter((i) => i.id !== id)
    drawer.value = false
  } catch {
    error.value = 'Failed to delete idea.'
  }
}

async function handleCreate() {
  try {
    const res = await ideasApi.create({
      title: createTitle.value,
      description: createDescription.value || undefined,
      priority: createPriority.value,
      tag_names: createTagIds.value.length > 0
        ? tags.value.filter((tag) => createTagIds.value.includes(tag.id)).map((tag) => tag.name)
        : undefined,
    })
    ideas.value.unshift(res.data)
    if (ideas.value.length > pageLimit.value) {
      ideas.value = ideas.value.slice(0, pageLimit.value)
    }
    pageTotal.value += 1
    pageOffset.value = 0
    createDialog.value = false
    createTitle.value = ''
    createDescription.value = ''
    createPriority.value = 'medium'
    createTagIds.value = []
  } catch {
    error.value = 'Failed to create idea.'
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
        <h1 class="text-h5 mb-1">Ideas</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">Capture, tag, filter, and promote ideas into projects.</p>
      </div>
      <v-btn color="primary" prepend-icon="$plus" @click="createDialog = true">Create idea</v-btn>
    </div>

    <v-card border flat class="mb-4">
      <v-card-text class="d-flex flex-wrap ga-3">
        <v-text-field v-model="query" prepend-inner-icon="$search" label="Search" hide-details />
        <v-select
          v-model="selectedStatus"
          :items="['active', 'paused', 'in_progress', 'completed']"
          clearable
          label="Status"
          hide-details
          max-width="220"
        />
        <v-select
          v-model="selectedTag"
          :items="tags"
          item-title="name"
          item-value="slug"
          clearable
          label="Tag"
          hide-details
          max-width="220"
        />
      </v-card-text>
    </v-card>

    <v-row>
      <v-col v-for="idea in filteredIdeas" :key="idea.id" cols="12" md="6" xl="4">
        <v-card border flat @click="openIdea(idea.id)">
          <v-card-title class="text-subtitle-1">{{ idea.title }}</v-card-title>
          <v-card-text>
            <p class="text-body-2 text-medium-emphasis">{{ idea.description || 'No description yet.' }}</p>
            <div class="d-flex flex-wrap ga-2">
              <v-chip v-for="tag in idea.tags" :key="tag.id" :color="tag.color ?? undefined" size="small" variant="tonal">
                {{ tag.name }}
              </v-chip>
            </div>
          </v-card-text>
          <v-card-actions>
            <v-chip size="small" color="primary" variant="tonal">{{ idea.status }}</v-chip>
            <v-spacer />
            <span class="text-caption text-medium-emphasis">Updated {{ formatDate(idea.updated_at) }}</span>
          </v-card-actions>
        </v-card>
      </v-col>
      <v-col v-if="!loading && filteredIdeas.length === 0" cols="12">
        <v-card border flat>
          <EmptyState
            icon="$idea"
            :title="hasActiveFilters ? 'No ideas match the filters' : 'No ideas yet'"
            :description="hasActiveFilters
              ? 'Adjust the search, status, or tag filters to widen the list.'
              : 'Capture the first idea so it can be evaluated, tagged, and promoted into project work.'"
            :action-label="hasActiveFilters ? 'Clear filters' : 'Create idea'"
            @action="hasActiveFilters ? clearFilters() : (createDialog = true)"
          />
        </v-card>
      </v-col>
    </v-row>

    <PaginationControls
      :offset="pageOffset"
      :limit="pageLimit"
      :total="pageTotal"
      :loading="loading"
      @page-change="handlePageChange"
    />

    <v-navigation-drawer v-model="drawer" temporary location="right" width="420">
      <template v-if="activeIdea">
        <v-toolbar flat>
          <v-toolbar-title>Idea detail</v-toolbar-title>
          <v-btn icon="$delete" variant="text" title="Delete idea" aria-label="Delete idea" @click="handleDelete(activeIdea.id)" />
          <v-btn icon="$close" variant="text" @click="drawer = false" />
        </v-toolbar>
        <div class="pa-4">
          <h2 class="text-h6 mb-2">{{ activeIdea.title }}</h2>
          <p class="text-body-2 text-medium-emphasis mb-4">{{ activeIdea.description }}</p>
          <v-select
            :model-value="activeIdea.status"
            :items="['active', 'paused', 'in_progress', 'completed']"
            label="Status"
            @update:model-value="(val: string) => handleStatusChange(activeIdea!.id, val)"
          />
          <div class="mt-4">
            <p class="text-caption text-medium-emphasis mb-2">Tags</p>
            <div class="d-flex flex-wrap ga-2">
              <v-chip v-for="tag in activeIdea.tags" :key="tag.id" :color="tag.color ?? undefined" size="small" variant="tonal">
                {{ tag.name }}
              </v-chip>
            </div>
          </div>
        </div>
      </template>
    </v-navigation-drawer>

    <v-dialog v-model="createDialog" max-width="520">
      <v-card title="Create idea">
        <v-card-text>
          <v-text-field v-model="createTitle" label="Title" />
          <v-textarea v-model="createDescription" label="Description" rows="3" />
          <v-select
            v-model="createPriority"
            :items="['low', 'medium', 'high']"
            label="Priority"
          />
          <v-autocomplete
            v-model="createTagIds"
            :items="tags"
            item-title="name"
            item-value="id"
            label="Tags"
            multiple
            chips
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="createDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="tonal" :disabled="!createTitle" @click="handleCreate">Create idea</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
