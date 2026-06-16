<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { ideasApi, tagsApi } from '@/api/modules'
import type { IdeaRead, TagRead } from '@/types/api'

const ideas = ref<IdeaRead[]>([])
const tags = ref<TagRead[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

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

const filteredIdeas = computed(() =>
  ideas.value.filter((idea) => {
    const matchesQuery = !query.value || idea.title.toLowerCase().includes(query.value.toLowerCase())
    const matchesStatus = !selectedStatus.value || idea.status === selectedStatus.value
    const matchesTag = !selectedTag.value || idea.tags.some((tag) => tag.slug === selectedTag.value)
    return matchesQuery && matchesStatus && matchesTag
  }),
)

const activeIdea = computed(() => ideas.value.find((idea) => idea.id === activeIdeaId.value))

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    const [ideasRes, tagsRes] = await Promise.all([ideasApi.list(), tagsApi.list()])
    ideas.value = ideasRes.data
    tags.value = tagsRes.data
  } catch (e) {
    error.value = 'Failed to load ideas. Please try again.'
  } finally {
    loading.value = false
  }
})

function openIdea(id: string) {
  activeIdeaId.value = id
  drawer.value = true
}

async function handleStatusChange(id: string, status: string) {
  try {
    const res = await ideasApi.updateStatus(id, { status })
    const idx = ideas.value.findIndex((i) => i.id === id)
    if (idx !== -1) ideas.value[idx] = res.data
  } catch {
    error.value = 'Failed to update status.'
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
      tag_ids: createTagIds.value.length > 0 ? createTagIds.value : undefined,
    })
    ideas.value.unshift(res.data)
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
      <v-btn color="primary" prepend-icon="$plus" @click="createDialog = true">Create</v-btn>
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
            <p class="text-body-2 text-medium-emphasis">{{ idea.description }}</p>
            <div class="d-flex flex-wrap ga-2">
              <v-chip v-for="tag in idea.tags" :key="tag.id" :color="tag.color" size="small" variant="tonal">
                {{ tag.name }}
              </v-chip>
            </div>
          </v-card-text>
          <v-card-actions>
            <v-chip size="small" color="primary" variant="tonal">{{ idea.status }}</v-chip>
            <v-spacer />
            <span class="text-caption text-medium-emphasis">{{ idea.updated_at }}</span>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-navigation-drawer v-model="drawer" temporary location="right" width="420">
      <template v-if="activeIdea">
        <v-toolbar flat>
          <v-toolbar-title>Idea detail</v-toolbar-title>
          <v-btn icon="$delete" variant="text" @click="handleDelete(activeIdea.id)" />
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
              <v-chip v-for="tag in activeIdea.tags" :key="tag.id" :color="tag.color" size="small" variant="tonal">
                {{ tag.name }}
              </v-chip>
            </div>
          </div>
        </div>
      </template>
    </v-navigation-drawer>

    <v-dialog v-model="createDialog" max-width="520">
      <v-card title="Create Idea">
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
          <v-btn color="primary" variant="tonal" :disabled="!createTitle" @click="handleCreate">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>
