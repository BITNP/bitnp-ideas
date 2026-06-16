<script setup lang="ts">
import { computed, ref } from 'vue'

import { useWorkspaceStore } from '@/stores/workspace'

const store = useWorkspaceStore()
const query = ref('')
const selectedStatus = ref<string | null>(null)
const selectedTag = ref<string | null>(null)
const drawer = ref(false)
const activeIdeaId = ref<string | null>(null)

const filteredIdeas = computed(() =>
  store.ideas.filter((idea) => {
    const matchesQuery = !query.value || idea.title.toLowerCase().includes(query.value.toLowerCase())
    const matchesStatus = !selectedStatus.value || idea.status === selectedStatus.value
    const matchesTag = !selectedTag.value || idea.tags.some((tag) => tag.slug === selectedTag.value)
    return matchesQuery && matchesStatus && matchesTag
  }),
)

const activeIdea = computed(() => store.ideas.find((idea) => idea.id === activeIdeaId.value))

function openIdea(id: string) {
  activeIdeaId.value = id
  drawer.value = true
}
</script>

<template>
  <div class="page-shell">
    <div class="toolbar-row mb-4">
      <div>
        <h1 class="text-h5 mb-1">Ideas</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">Capture, tag, filter, and promote ideas into projects.</p>
      </div>
      <v-btn color="primary" prepend-icon="$plus">Create</v-btn>
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
          :items="store.tags"
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
            <span class="text-caption text-medium-emphasis">{{ idea.updatedAt }}</span>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-navigation-drawer v-model="drawer" temporary location="right" width="420">
      <template v-if="activeIdea">
        <v-toolbar flat>
          <v-toolbar-title>Idea detail</v-toolbar-title>
          <v-btn icon="$close" variant="text" @click="drawer = false" />
        </v-toolbar>
        <div class="pa-4">
          <h2 class="text-h6 mb-2">{{ activeIdea.title }}</h2>
          <p class="text-body-2 text-medium-emphasis">{{ activeIdea.description }}</p>
          <v-select
            :model-value="activeIdea.status"
            :items="['active', 'paused', 'in_progress', 'completed']"
            label="Status"
          />
          <v-autocomplete
            :items="store.tags"
            :model-value="activeIdea.tags"
            item-title="name"
            label="Tags"
            multiple
            chips
          />
        </div>
      </template>
    </v-navigation-drawer>
  </div>
</template>

