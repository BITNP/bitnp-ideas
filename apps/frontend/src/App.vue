<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useTheme } from 'vuetify'

import { useWorkspaceStore } from '@/stores/workspace'

const route = useRoute()
const theme = useTheme()
const store = useWorkspaceStore()
const drawer = ref(true)

const navItems = [
  { title: 'Dashboard', to: '/dashboard', icon: '$dashboard' },
  { title: 'Ideas', to: '/ideas', icon: '$idea' },
  { title: 'Projects', to: '/projects', icon: '$gantt' },
  { title: 'API Keys', to: '/api-keys', icon: '$key' },
  { title: 'Users', to: '/users', icon: '$users' },
  { title: 'Settings', to: '/settings', icon: '$settings' },
]

const title = computed(() => navItems.find((item) => route.path.startsWith(item.to))?.title ?? 'Dashboard')
const isDark = computed(() => theme.global.current.value.dark)

function toggleTheme() {
  theme.global.name.value = isDark.value ? 'ideasLight' : 'ideasDark'
}

onMounted(() => store.attachTags())
</script>

<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" width="268">
      <div class="pa-4">
        <div class="text-h6 font-weight-bold">BITNP IDEAS</div>
        <div class="text-caption text-medium-emphasis">Idea-Driven Execution</div>
      </div>

      <v-list nav density="compact">
        <v-list-item
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          rounded="lg"
        />
      </v-list>
    </v-navigation-drawer>

    <v-app-bar flat border>
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-toolbar-title>{{ title }}</v-toolbar-title>
      <v-spacer />
      <v-btn :icon="isDark ? '$sun' : '$moon'" variant="text" @click="toggleTheme" />
      <v-btn icon="$account" variant="text" to="/settings" />
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

