/* eslint-disable vue/one-component-per-file, vue/order-in-components, vue/require-prop-types */
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'

import AuditLogsPage from '../AuditLogsPage.vue'

const api = vi.hoisted(() => ({
  auditApi: {
    list: vi.fn(),
  },
}))

vi.mock('@/api/modules', () => api)
vi.mock('vuetify/components/VDateInput', () => ({
  VDateInput: {
    props: ['modelValue', 'label'],
    emits: ['update:modelValue'],
    template: `
      <label>
        <span>{{ label }}</span>
        <input
          :aria-label="label"
          :value="modelValue ?? ''"
          @input="$emit('update:modelValue', new Date($event.target.value + 'T00:00:00'))"
        />
      </label>
    `,
  },
}))

const fieldStub = defineComponent({
  props: ['modelValue', 'label'],
  emits: ['update:modelValue'],
  template: `
    <label>
      <span>{{ label }}</span>
      <input
        :aria-label="label"
        :value="modelValue ?? ''"
        @input="$emit('update:modelValue', $event.target.value)"
      />
    </label>
  `,
})

const dateFieldStub = defineComponent({
  props: ['modelValue', 'label'],
  emits: ['update:modelValue'],
  template: `
    <label>
      <span>{{ label }}</span>
      <input
        :aria-label="label"
        :value="modelValue ?? ''"
        @input="$emit('update:modelValue', new Date($event.target.value + 'T00:00:00'))"
      />
    </label>
  `,
})

const passthroughStub = defineComponent({
  props: ['title'],
  template: '<section><h2 v-if="title">{{ title }}</h2><slot /></section>',
})

const buttonStub = defineComponent({
  props: ['disabled'],
  emits: ['click'],
  template: '<button :disabled="disabled" @click="$emit(\'click\', $event)"><slot /></button>',
})

async function mountPage() {
  const wrapper = mount(AuditLogsPage, {
    global: {
      stubs: {
        PaginationControls: defineComponent({
          emits: ['page-change'],
          props: ['offset', 'limit', 'total'],
          template: '<div class="pagination-controls">{{ total }}</div>',
        }),
        VAlert: passthroughStub,
        VBtn: buttonStub,
        VCard: passthroughStub,
        VCardText: passthroughStub,
        VCardTitle: passthroughStub,
        VChip: passthroughStub,
        VDateInput: dateFieldStub,
        VDialog: passthroughStub,
        VSelect: fieldStub,
        VSpacer: passthroughStub,
        VTable: passthroughStub,
        VTextarea: fieldStub,
        VTextField: fieldStub,
        'v-alert': passthroughStub,
        'v-btn': buttonStub,
        'v-card': passthroughStub,
        'v-card-text': passthroughStub,
        'v-card-title': passthroughStub,
        'v-chip': passthroughStub,
        'v-date-input': dateFieldStub,
        'v-dialog': passthroughStub,
        'v-select': fieldStub,
        'v-spacer': passthroughStub,
        'v-table': passthroughStub,
        'v-textarea': fieldStub,
        'v-text-field': fieldStub,
      },
    },
  })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  api.auditApi.list.mockResolvedValue({ data: { data: [], total: 0 } })
})

describe('AuditLogsPage', () => {
  it('applies audit filters through the API', async () => {
    const wrapper = await mountPage()

    await wrapper.find('input[aria-label="Action"]').setValue('project.created')
    await wrapper.find('input[aria-label="Entity type"]').setValue('project')
    await wrapper.find('input[aria-label="Entity ID"]').setValue('project-1')
    await wrapper.find('input[aria-label="Actor user ID"]').setValue('user-1')
    await wrapper.find('input[aria-label="Created from"]').setValue('2026-06-01')
    await wrapper.find('input[aria-label="Created to"]').setValue('2026-06-18')
    await wrapper.findAll('button').find((button) => button.text() === 'Apply')?.trigger('click')
    await flushPromises()

    expect(api.auditApi.list).toHaveBeenLastCalledWith({
      offset: 0,
      limit: 25,
      action: 'project.created',
      entity_type: 'project',
      entity_id: 'project-1',
      actor_user_id: 'user-1',
      actor_api_key_id: undefined,
      created_from: '2026-06-01',
      created_to: '2026-06-18',
    })
  })

  it('clears filters and reloads the first page', async () => {
    const wrapper = await mountPage()

    await wrapper.find('input[aria-label="Action"]').setValue('api_key.created')
    await wrapper.findAll('button').find((button) => button.text() === 'Clear')?.trigger('click')
    await flushPromises()

    expect(api.auditApi.list).toHaveBeenLastCalledWith({
      offset: 0,
      limit: 25,
      action: undefined,
      entity_type: undefined,
      entity_id: undefined,
      actor_user_id: undefined,
      actor_api_key_id: undefined,
      created_from: undefined,
      created_to: undefined,
    })
  })
})
