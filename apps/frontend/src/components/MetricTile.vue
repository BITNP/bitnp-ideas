<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  icon: string
  tone?: string
}>()
</script>

<template>
  <v-card border flat>
    <v-card-text class="d-flex align-center justify-space-between ga-3">
      <div>
        <div class="text-caption text-medium-emphasis">{{ label }}</div>
        <div class="text-h5 font-weight-bold mt-1">{{ value }}</div>
      </div>
      <v-avatar :color="tone ?? 'primary'" variant="tonal">
        <v-icon :icon="icon" />
      </v-avatar>
    </v-card-text>
  </v-card>
</template>

