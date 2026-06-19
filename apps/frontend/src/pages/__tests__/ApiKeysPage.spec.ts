/* eslint-disable vue/one-component-per-file, vue/require-prop-types */
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'

import ApiKeysPage from '../ApiKeysPage.vue'

const api = vi.hoisted(() => ({
  apiKeysApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    revoke: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('@/api/modules', () => api)

const apiKey = {
  id: 'key-1',
  name: 'AI intake workflow',
  key_id: 'bik_public_id',
  secret_last4: 'abcd',
  scopes: ['ideas:read', 'ideas:write'],
  allowed_entities: ['idea'],
  is_active: true,
  last_used_at: null,
  revoked_at: null,
  created_at: '2026-06-19T00:00:00Z',
}

const inactiveApiKey = {
  ...apiKey,
  id: 'key-inactive',
  name: 'Paused workflow',
  key_id: 'bik_inactive',
  is_active: false,
}

const revokedApiKey = {
  ...apiKey,
  id: 'key-revoked',
  name: 'Retired workflow',
  key_id: 'bik_revoked',
  is_active: false,
  revoked_at: '2026-06-19T08:00:00Z',
}

const fieldStub = defineComponent({
  props: ['modelValue', 'label', 'disabled'],
  emits: ['update:modelValue', 'click:appendInner'],
  template: `
    <label>
      <span>{{ label }}</span>
      <input
        :aria-label="label"
        :disabled="disabled"
        :value="modelValue ?? ''"
        @input="$emit('update:modelValue', $event.target.value)"
      />
      <button
        v-if="$attrs.appendInnerIcon"
        type="button"
        @click="$emit('click:appendInner')"
      >
        append
      </button>
    </label>
  `,
})

const passthroughStub = defineComponent({
  props: ['title'],
  template: '<section><h2 v-if="title">{{ title }}</h2><slot /></section>',
})

const dialogStub = defineComponent({
  props: ['modelValue'],
  template: '<section v-if="modelValue" class="dialog"><slot /></section>',
})

const buttonStub = defineComponent({
  props: ['disabled'],
  emits: ['click'],
  template: '<button :disabled="disabled" @click="$emit(\'click\', $event)"><slot /></button>',
})

async function mountPage() {
  const wrapper = mount(ApiKeysPage, {
    global: {
      stubs: {
        PaginationControls: defineComponent({
          props: ['total'],
          template: '<div class="pagination-controls">{{ total }}</div>',
        }),
        VAlert: passthroughStub,
        VAvatar: passthroughStub,
        VBtn: buttonStub,
        VCard: passthroughStub,
        VCardActions: passthroughStub,
        VCardText: passthroughStub,
        VChip: passthroughStub,
        VDialog: dialogStub,
        VIcon: passthroughStub,
        VSpacer: passthroughStub,
        VSelect: fieldStub,
        VTable: passthroughStub,
        VTextField: fieldStub,
        'v-alert': passthroughStub,
        'v-avatar': passthroughStub,
        'v-btn': buttonStub,
        'v-card': passthroughStub,
        'v-card-actions': passthroughStub,
        'v-card-text': passthroughStub,
        'v-chip': passthroughStub,
        'v-dialog': dialogStub,
        'v-icon': passthroughStub,
        'v-spacer': passthroughStub,
        'v-select': fieldStub,
        'v-table': passthroughStub,
        'v-text-field': fieldStub,
      },
    },
  })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  vi.clearAllMocks()
  api.apiKeysApi.list.mockResolvedValue({ data: { data: [], total: 0 } })
  api.apiKeysApi.create.mockResolvedValue({
    data: {
      api_key: apiKey,
      secret: 'biks_one_time_secret',
    },
  })
})

describe('ApiKeysPage', () => {
  it('shows the one-time signing secret after creating an API key', async () => {
    const wrapper = await mountPage()

    await wrapper.findAll('button').find((button) => button.text() === 'Create key')?.trigger('click')
    const createDialog = wrapper.find('.dialog')
    await createDialog.find('input[aria-label="Name"]').setValue('AI intake workflow')
    await createDialog.find('input[aria-label="Scopes (comma-separated)"]').setValue('ideas:read, ideas:write')
    await createDialog.findAll('button').find((button) => button.text() === 'Create key')?.trigger('click')
    await flushPromises()

    expect(api.apiKeysApi.create).toHaveBeenCalledWith({
      name: 'AI intake workflow',
      scopes: ['ideas:read', 'ideas:write'],
    })
    expect(wrapper.text()).toContain('API key created')
    const keyIdInput = wrapper.find('input[aria-label="Key ID"]').element as HTMLInputElement
    const secretInput = wrapper.find('input[aria-label="Signing secret"]').element as HTMLInputElement
    expect(keyIdInput.value).toBe('bik_public_id')
    expect(secretInput.value).toBe('biks_one_time_secret')
    expect(wrapper.text()).toContain('This signing secret is shown once.')
  })

  it('separates inactive API keys from permanently revoked keys', async () => {
    api.apiKeysApi.list.mockResolvedValueOnce({
      data: { data: [inactiveApiKey, revokedApiKey], total: 2 },
    })
    api.apiKeysApi.update.mockResolvedValue({ data: { message: 'api key updated' } })

    const wrapper = await mountPage()

    expect(wrapper.text()).toContain('inactive')
    expect(wrapper.text()).toContain('revoked')

    await wrapper.findAll('button').find((button) => button.text() === 'Activate')?.trigger('click')

    expect(api.apiKeysApi.update).toHaveBeenCalledWith('key-inactive', { is_active: true })
    expect(wrapper.findAll('button').filter((button) => button.text() === 'Revoke' && button.attributes('disabled') !== undefined)).toHaveLength(1)
  })
})
