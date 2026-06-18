<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  offset: number
  limit: number
  total: number
  loading?: boolean
}>(), {
  loading: false,
})

const emit = defineEmits<{
  'page-change': [value: { offset: number; limit: number }]
}>()

const limitOptions = [10, 25, 50, 100]
const currentPage = computed({
  get: () => Math.floor(props.offset / props.limit) + 1,
  set: (page: number) => changePage(page),
})
const pageCount = computed(() => Math.max(Math.ceil(props.total / props.limit), 1))
const startRow = computed(() => props.total === 0 ? 0 : props.offset + 1)
const endRow = computed(() => Math.min(props.offset + props.limit, props.total))

function changeLimit(value: number | null) {
  emit('page-change', { offset: 0, limit: value ?? props.limit })
}

function changePage(page: number) {
  emit('page-change', { offset: (page - 1) * props.limit, limit: props.limit })
}
</script>

<template>
  <div class="d-flex flex-column align-center ga-2 mt-4">
    <div class="d-flex flex-wrap align-center justify-center ga-3">
      <v-select
        :model-value="limit"
        :items="limitOptions"
        label="Rows"
        hide-details
        density="compact"
        variant="underlined"
        max-width="120"
        @update:model-value="changeLimit"
      />
      <v-pagination
        v-model="currentPage"
        :length="pageCount"
        :disabled="loading"
        density="comfortable"
        total-visible="6"
      />
    </div>
    <div class="text-caption text-medium-emphasis">
      {{ startRow }}-{{ endRow }} of {{ total }}
    </div>
  </div>
</template>

