<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDisplay, useTheme } from 'vuetify'
import { useAuthStore } from '@/stores/auth'

const LAYOUT_BREAKPOINT = 960

const route = useRoute()
const theme = useTheme()
const display = useDisplay()
const auth = useAuthStore()
const isDesktopLayout = computed(() => display.width.value >= LAYOUT_BREAKPOINT)
const drawer = ref(isDesktopLayout.value)

const navItems = [
  { title: 'Dashboard', to: '/dashboard', icon: '$dashboard' },
  { title: 'Ideas', to: '/ideas', icon: '$idea' },
  { title: 'Projects', to: '/projects', icon: '$gantt' },
  { title: 'API Keys', to: '/api-keys', icon: '$key' },
  { title: 'Users', to: '/users', icon: '$users' },
]

const title = computed(() => navItems.find((item) => route.path.startsWith(item.to))?.title ?? 'Dashboard')
const isDark = computed(() => theme.global.current.value.dark)

watch(isDesktopLayout, (desktop) => {
  drawer.value = desktop
}, { immediate: true })

function toggleTheme() {
  theme.global.name.value = isDark.value ? 'ideasLight' : 'ideasDark'
}

async function handleLogout() {
  await auth.logout()
}
</script>

<template>
  <v-app>
    <!-- Full-screen blank layout (login page) — no chrome -->
    <template v-if="route.meta.layout === 'blank'">
      <v-main>
        <router-view />
      </v-main>
    </template>

    <!-- Default layout with sidebar + app bar -->
    <template v-else-if="auth.ready">
      <v-navigation-drawer
        v-model="drawer"
        :temporary="!isDesktopLayout"
        :permanent="isDesktopLayout"
        :mobile-breakpoint="LAYOUT_BREAKPOINT"
        width="268"
      >
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
    </template>

    <!-- Loading state while restoring session -->
    <div v-else class="d-flex align-center justify-center h-screen">
      <v-progress-circular indeterminate color="primary" size="48" />
    </div>
  </v-app>
</template>
