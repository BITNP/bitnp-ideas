<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useTheme } from 'vuetify'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const theme = useTheme()
const auth = useAuthStore()
const drawer = ref(window.innerWidth >= 960)

const navItems = [
  { title: 'Dashboard', to: '/dashboard', icon: '$dashboard' },
  { title: 'Ideas', to: '/ideas', icon: '$idea' },
  { title: 'Projects', to: '/projects', icon: '$gantt' },
  { title: 'API Keys', to: '/api-keys', icon: '$key' },
  { title: 'Users', to: '/users', icon: '$users' },
]

const title = computed(() => navItems.find((item) => route.path.startsWith(item.to))?.title ?? 'Dashboard')
const isDark = computed(() => theme.global.current.value.dark)

function toggleTheme() {
  theme.global.name.value = isDark.value ? 'ideasLight' : 'ideasDark'
}

async function handleLogout() {
  await auth.logout()
}
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

      <v-menu v-if="auth.isAuthenticated">
        <template #activator="{ props: menuProps }">
          <v-btn
            icon="$account"
            variant="text"
            v-bind="menuProps"
          />
        </template>
        <v-list density="compact">
          <v-list-item :title="auth.user?.display_name ?? ''" :subtitle="auth.user?.email ?? ''" />
          <v-divider />
          <v-list-item title="Sign out" @click="handleLogout" />
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>
