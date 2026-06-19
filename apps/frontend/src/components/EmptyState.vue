<script setup lang="ts">
defineProps<{
  icon?: string
  title: string
  description: string
  actionLabel?: string
}>()

const emit = defineEmits<{
  action: []
}>()
</script>

<template>
  <div class="empty-state">
    <v-avatar v-if="icon" color="primary" variant="tonal" size="40" class="mb-3">
      <v-icon :icon="icon" />
    </v-avatar>
    <div class="text-subtitle-1 font-weight-medium mb-1">{{ title }}</div>
    <p class="text-body-2 text-medium-emphasis mb-0">{{ description }}</p>
    <v-btn
      v-if="actionLabel"
      color="primary"
      variant="tonal"
      class="mt-4"
      @click="emit('action')"
    >
      {{ actionLabel }}
    </v-btn>
  </div>
</template>
