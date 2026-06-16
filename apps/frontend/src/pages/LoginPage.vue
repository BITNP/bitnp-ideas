<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  const { code, state } = route.query

  // ── OAuth callback flow ─────────────────────────────────
  if (code && state) {
    loading.value = true
    try {
      await auth.handleCallback(code as string, state as string)
      router.replace('/dashboard')
    } catch (err) {
      error.value = 'SSO login failed. Please try again.'
      console.error('Callback error:', err)
    } finally {
      loading.value = false
    }
    return
  }

  // ── Already authenticated → redirect ────────────────────
  if (auth.isAuthenticated) {
    router.replace('/dashboard')
  }
})

async function startLogin() {
  loading.value = true
  error.value = null
  try {
    await auth.login()
  } catch (err) {
    error.value = 'Failed to initiate login. Please try again.'
    console.error('Login error:', err)
    loading.value = false
  }
}
</script>

<template>
  <div class="page-shell">
    <v-row justify="center">
      <v-col cols="12" md="6" lg="4">
        <v-card border flat>
          <v-card-title class="text-center text-h5">BITNP IDEAS</v-card-title>
          <v-card-subtitle class="text-center">Idea-Driven Execution</v-card-subtitle>
          <v-card-text class="pt-4">
            <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4">
              {{ error }}
            </v-alert>

            <v-progress-linear v-if="loading" indeterminate class="mb-4" color="primary" />

            <v-btn
              block
              color="primary"
              size="large"
              prepend-icon="$account"
              :loading="loading"
              :disabled="loading"
              @click="startLogin"
            >
              Sign in with BITNP SSO
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
