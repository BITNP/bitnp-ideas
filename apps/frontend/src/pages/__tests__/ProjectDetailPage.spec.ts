/* eslint-disable vue/one-component-per-file, vue/order-in-components, vue/require-prop-types */
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { defineComponent } from 'vue'

import ProjectDetailPage from '../ProjectDetailPage.vue'

const api = vi.hoisted(() => ({
  projectsApi: {
    get: vi.fn(),
    addMember: vi.fn(),
    removeMember: vi.fn(),
    listIdeas: vi.fn(),
    addIdea: vi.fn(),
    removeIdea: vi.fn(),
    update: vi.fn(),
  },
  tasksApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  ganttApi: {
    get: vi.fn(),
  },
  activityApi: {
    list: vi.fn(),
  },
  linksApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
  usersApi: {
    list: vi.fn(),
  },
  ideasApi: {
    list: vi.fn(),
  },
}))

vi.mock('@/api/modules', () => api)
let routeName = 'project-detail'

vi.mock('vue-router', () => ({
  useRoute: () => ({ name: routeName, params: { id: 'project-1' } }),
}))
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
          @input="$emit('update:modelValue', $event.target.value)"
        />
      </label>
    `,
  },
}))
vi.mock('@/components/GanttBoard.vue', () => ({
  __esModule: true,
  __isTeleport: false,
  default: defineComponent({
    props: ['readonly'],
    emits: ['refresh', 'error'],
    template: `
      <div data-test="gantt-board" :data-readonly="readonly ? 'true' : 'false'">
        <button data-test="gantt-refresh" @click="$emit('refresh')">refresh</button>
        <button data-test="gantt-error" @click="$emit('error', 'Gantt failed')">error</button>
      </div>
    `,
  }),
}))
vi.mock('@/components/MetricTile.vue', () => ({
  default: defineComponent({
    props: ['label', 'value'],
    template: '<div class="metric-tile">{{ label }} {{ value }}</div>',
  }),
}))
vi.mock('@/components/PaginationControls.vue', () => ({
  default: defineComponent({
    emits: ['page-change'],
    props: ['offset', 'limit', 'total'],
    template: '<button class="pagination-controls" @click="$emit(\'page-change\', { offset: offset + limit, limit })">{{ total }}</button>',
  }),
}))

const project = {
  id: 'project-1',
  key: 'EXEC',
  name: 'Execution Project',
  description: 'Build the thing.',
  status: 'active',
  owner: { id: 'user-admin', name: 'Admin' },
  progress: 25,
  start_date: null,
  target_end_date: null,
  members: [
    { id: 'user-dev', name: 'Developer' },
    { id: 'user-admin', name: 'Admin' },
  ],
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-02T00:00:00Z',
}

const updatedProject = {
  ...project,
  members: [...project.members, { id: 'user-outsider', name: 'Outsider' }],
}

const task = {
  id: 'task-1',
  project_id: 'project-1',
  title: 'Design API',
  description: 'Shape the endpoints.',
  status: 'todo',
  assignee: { id: 'user-dev', name: 'Developer' },
  start_date: '2026-07-01',
  end_date: '2026-07-03',
  progress: 10,
  version: 1,
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-02T00:00:00Z',
}

const updatedTask = {
  ...task,
  title: 'Refined API',
  status: 'review',
  progress: 55,
  version: 2,
}

const idea = {
  id: 'idea-1',
  title: 'Connect planning',
  description: 'Turn planning into project work.',
  status: 'active',
  priority: 'medium',
  tags: [],
  creator: { id: 'user-dev', name: 'Developer' },
  linked_project: null,
  linked_project_url: null,
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-02T00:00:00Z',
}

const link = {
  id: 'link-1',
  entity_type: 'project',
  entity_id: 'project-1',
  url: 'https://github.com/BITNP/ideas',
  title: 'Repository',
  description: null,
  image_url: null,
  site_name: null,
  link_type: 'github_repo',
  created_at: '2026-06-01T00:00:00Z',
}

const adminUser = {
  id: 'user-admin',
  email: 'admin@example.test',
  display_name: 'Admin',
  global_role: 'administrator',
  is_active: true,
}

const developerUser = {
  id: 'user-dev',
  email: 'developer@example.test',
  display_name: 'Developer',
  global_role: 'developer',
  is_active: true,
}

const outsiderUser = {
  id: 'user-outsider',
  email: 'outsider@example.test',
  display_name: 'Outsider',
  global_role: 'developer',
  is_active: true,
}

function page<T>(data: T[]) {
  return { data: { data, total: data.length } }
}

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

const sliderStub = defineComponent({
  props: ['modelValue', 'label'],
  emits: ['update:modelValue'],
  template: `
    <label>
      <span>{{ label }}</span>
      <input
        :aria-label="label"
        type="number"
        :value="modelValue ?? ''"
        @input="$emit('update:modelValue', Number($event.target.value))"
      />
    </label>
  `,
})

const dialogStub = defineComponent({
  props: ['modelValue', 'title'],
  template: '<section v-if="modelValue" class="dialog"><h2>{{ title }}</h2><slot /></section>',
})

const drawerStub = defineComponent({
  props: ['modelValue'],
  template: '<aside v-if="modelValue" data-test="task-drawer"><slot /></aside>',
})

const passthroughStub = defineComponent({
  props: ['title', 'subtitle'],
  template: '<div><strong v-if="title">{{ title }}</strong><small v-if="subtitle">{{ subtitle }}</small><slot /></div>',
})

const buttonStub = defineComponent({
  props: ['disabled', 'icon'],
  emits: ['click'],
  template: '<button :data-icon="icon" :disabled="disabled" @click="$emit(\'click\', $event)"><slot /></button>',
})

async function mountPage(user = adminUser) {
  localStorage.setItem('access_token', 'token')
  localStorage.setItem('user', JSON.stringify(user))
  const pinia = createPinia()
  setActivePinia(pinia)
  const wrapper = mount(ProjectDetailPage, {
    global: {
      plugins: [pinia],
      stubs: {
        VAlert: passthroughStub,
        VAutocomplete: fieldStub,
        VBtn: buttonStub,
        'v-alert': passthroughStub,
        'v-autocomplete': fieldStub,
        'v-btn': buttonStub,
        VCard: defineComponent({
          props: ['title'],
          template: '<section><h2 v-if="title">{{ title }}</h2><slot /></section>',
        }),
        VCardActions: passthroughStub,
        VCardText: passthroughStub,
        VCardTitle: passthroughStub,
        VChip: passthroughStub,
        VCol: passthroughStub,
        VDateInput: fieldStub,
        VDialog: dialogStub,
        VList: passthroughStub,
        VListItem: defineComponent({
          props: ['title', 'subtitle'],
          emits: ['click'],
          template: '<div class="list-item" @click="$emit(\'click\', $event)"><span>{{ title }}</span><span>{{ subtitle }}</span><slot name="append" /></div>',
        }),
        VNavigationDrawer: drawerStub,
        VRow: passthroughStub,
        VSelect: fieldStub,
        VSlider: sliderStub,
        VSpacer: passthroughStub,
        VTab: passthroughStub,
        VTabs: passthroughStub,
        VTable: passthroughStub,
        VTextarea: fieldStub,
        VTimeline: passthroughStub,
        VTimelineItem: passthroughStub,
        VToolbar: passthroughStub,
        VToolbarTitle: passthroughStub,
        VWindow: passthroughStub,
        VWindowItem: passthroughStub,
        'v-card': defineComponent({
          props: ['title'],
          template: '<section><h2 v-if="title">{{ title }}</h2><slot /></section>',
        }),
        'v-card-actions': passthroughStub,
        'v-card-text': passthroughStub,
        'v-card-title': passthroughStub,
        'v-chip': passthroughStub,
        'v-col': passthroughStub,
        'v-date-input': fieldStub,
        'v-dialog': dialogStub,
        'v-list': passthroughStub,
        'v-list-item': defineComponent({
          props: ['title', 'subtitle'],
          emits: ['click'],
          template: '<div class="list-item" @click="$emit(\'click\', $event)"><span>{{ title }}</span><span>{{ subtitle }}</span><slot name="append" /></div>',
        }),
        'v-navigation-drawer': drawerStub,
        'v-row': passthroughStub,
        'v-select': fieldStub,
        'v-slider': sliderStub,
        'v-spacer': passthroughStub,
        'v-tab': passthroughStub,
        'v-tabs': passthroughStub,
        'v-table': passthroughStub,
        'v-text-field': fieldStub,
        'v-textarea': fieldStub,
        'v-timeline': passthroughStub,
        'v-timeline-item': passthroughStub,
        'v-toolbar': passthroughStub,
        'v-toolbar-title': passthroughStub,
        'v-window': passthroughStub,
        'v-window-item': passthroughStub,
      },
    },
  })
  await flushPromises()
  return wrapper
}

function visibleButtonLabels(wrapper: Awaited<ReturnType<typeof mountPage>>) {
  return wrapper.findAll('button').map((button) => button.text()).filter(Boolean)
}

beforeEach(() => {
  routeName = 'project-detail'
  localStorage.clear()
  api.projectsApi.get.mockResolvedValue({ data: project })
  api.projectsApi.addMember.mockResolvedValue({ data: { message: 'member added' } })
  api.projectsApi.removeMember.mockResolvedValue({ data: { message: 'member removed' } })
  api.projectsApi.listIdeas.mockResolvedValue(page([]))
  api.projectsApi.addIdea.mockResolvedValue({ data: { message: 'idea linked' } })
  api.projectsApi.removeIdea.mockResolvedValue({ data: { message: 'idea unlinked' } })
  api.projectsApi.update.mockResolvedValue({ data: project })
  api.tasksApi.list.mockResolvedValue(page([task]))
  api.tasksApi.create.mockResolvedValue({ data: task })
  api.tasksApi.update.mockResolvedValue({ data: updatedTask })
  api.tasksApi.delete.mockResolvedValue({ data: { message: 'task archived' } })
  api.ganttApi.get.mockResolvedValue({ data: { project, tasks: [task], dependencies: [] } })
  api.activityApi.list.mockResolvedValue(page([]))
  api.linksApi.list.mockResolvedValue(page([]))
  api.linksApi.create.mockResolvedValue({ data: link })
  api.linksApi.delete.mockResolvedValue({ data: { message: 'link deleted' } })
  api.usersApi.list.mockResolvedValue(page([
    {
      id: 'user-outsider',
      email: 'outsider@example.test',
      display_name: 'Outsider',
      global_role: 'developer',
      is_active: true,
    },
  ]))
  api.ideasApi.list.mockResolvedValue(page([idea]))
})

describe('ProjectDetailPage', () => {
  it('opens the task drawer and saves task edits through the API', async () => {
    const wrapper = await mountPage()

    await wrapper.find('.table-row-action').trigger('click')
    const drawer = wrapper.find('[data-test="task-drawer"]')
    expect(drawer.exists()).toBe(true)

    await drawer.find('input[aria-label="Title"]').setValue('Refined API')
    await drawer.find('input[aria-label="Status"]').setValue('review')
    await drawer.find('input[aria-label="Progress"]').setValue('55')
    await drawer.findAll('button').find((button) => button.text() === 'Save task')?.trigger('click')
    await flushPromises()

    expect(api.tasksApi.update).toHaveBeenCalledWith('task-1', expect.objectContaining({
      title: 'Refined API',
      status: 'review',
      progress: 55,
      version: 1,
    }))
  })

  it('adds a project member using the member autocomplete flow', async () => {
    api.projectsApi.get
      .mockResolvedValueOnce({ data: project })
      .mockResolvedValueOnce({ data: updatedProject })
    const wrapper = await mountPage()

    await wrapper.findAll('button').find((button) => button.text() === 'Add member')?.trigger('click')
    await wrapper.find('.dialog input[aria-label="User"]').setValue('user-outsider')
    await wrapper.findAll('.dialog button').find((button) => button.text() === 'Add')?.trigger('click')
    await flushPromises()

    expect(api.projectsApi.addMember).toHaveBeenCalledWith('project-1', 'user-outsider')
    expect(api.projectsApi.get).toHaveBeenCalledTimes(2)
  })

  it('links ideas and creates external links through Project Detail dialogs', async () => {
    const wrapper = await mountPage()

    await wrapper.findAll('button').find((button) => button.text() === 'Link idea')?.trigger('click')
    await wrapper.find('.dialog input[aria-label="Idea"]').setValue('idea-1')
    await wrapper.find('.dialog input[aria-label="Relation"]').setValue('origin')
    await wrapper.findAll('.dialog button').find((button) => button.text() === 'Link')?.trigger('click')
    await flushPromises()

    expect(api.projectsApi.addIdea).toHaveBeenCalledWith('project-1', 'idea-1', 'origin')

    await wrapper.findAll('button').find((button) => button.text() === 'Add link')?.trigger('click')
    await wrapper.find('.dialog input[aria-label="URL"]').setValue('https://github.com/BITNP/ideas')
    await wrapper.find('.dialog input[aria-label="Title"]').setValue('Repository')
    await wrapper.find('.dialog input[aria-label="Type"]').setValue('github_repo')
    await wrapper.findAll('.dialog button').find((button) => button.text() === 'Create')?.trigger('click')
    await flushPromises()

    expect(api.linksApi.create).toHaveBeenCalledWith('project', 'project-1', {
      url: 'https://github.com/BITNP/ideas',
      title: 'Repository',
      description: undefined,
      link_type: 'github_repo',
    })
  })

  it('lets project members edit work without project administration controls', async () => {
    const wrapper = await mountPage(developerUser)
    const labels = visibleButtonLabels(wrapper)

    expect(labels).toContain('Add task')
    expect(labels).toContain('Add link')
    expect(labels).not.toContain('Add member')
    expect(labels).not.toContain('Link idea')
    expect(wrapper.text()).not.toContain('Settings')

    await wrapper.find('.table-row-action').trigger('click')
    const drawer = wrapper.find('[data-test="task-drawer"]')
    await drawer.find('input[aria-label="Title"]').setValue('Developer update')
    await drawer.findAll('button').find((button) => button.text() === 'Save task')?.trigger('click')
    await flushPromises()

    expect(api.tasksApi.update).toHaveBeenCalledWith('task-1', expect.objectContaining({
      title: 'Developer update',
      version: 1,
    }))
  })

  it('keeps non-members in a read-only project detail state', async () => {
    routeName = 'project-gantt'
    const wrapper = await mountPage(outsiderUser)
    await flushPromises()
    const labels = visibleButtonLabels(wrapper)

    expect(labels).not.toContain('Add task')
    expect(labels).not.toContain('Add member')
    expect(labels).not.toContain('Link idea')
    expect(labels).not.toContain('Add link')
    expect(wrapper.find('[data-test="gantt-board"]').attributes('data-readonly')).toBe('true')

    await wrapper.find('.table-row-action').trigger('click')
    const drawer = wrapper.find('[data-test="task-drawer"]')
    expect(drawer.findAll('button').some((button) => button.text() === 'Save task')).toBe(false)
  })

  it('uses pagination controls to fetch the next task page', async () => {
    const wrapper = await mountPage()

    await wrapper.find('.pagination-controls').trigger('click')
    await flushPromises()

    expect(api.tasksApi.list).toHaveBeenLastCalledWith('project-1', { offset: 25, limit: 25 })
  })

  it('unlinks ideas and deletes external links from their lists', async () => {
    api.projectsApi.listIdeas.mockResolvedValue(page([idea]))
    api.linksApi.list.mockResolvedValue(page([link]))
    const wrapper = await mountPage()

    await (wrapper.vm as unknown as { fetchIdeas: () => Promise<void> }).fetchIdeas()
    await flushPromises()
    await wrapper.findAll('button[data-icon="$delete"]').at(2)?.trigger('click')
    await flushPromises()

    expect(api.projectsApi.removeIdea).toHaveBeenCalledWith('project-1', 'idea-1')

    await (wrapper.vm as unknown as { fetchLinks: () => Promise<void> }).fetchLinks()
    await flushPromises()
    await wrapper.findAll('button[data-icon="$delete"]').at(3)?.trigger('click')
    await flushPromises()

    expect(api.linksApi.delete).toHaveBeenCalledWith('link-1')
  })

  it('refreshes gantt data from GanttBoard events and surfaces gantt errors', async () => {
    routeName = 'project-gantt'
    const wrapper = await mountPage()
    await flushPromises()

    expect(api.ganttApi.get).toHaveBeenCalledTimes(1)
    await wrapper.find('[data-test="gantt-refresh"]').trigger('click')
    await flushPromises()
    expect(api.ganttApi.get).toHaveBeenCalledTimes(2)

    await wrapper.find('[data-test="gantt-error"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Gantt failed')
    expect(api.ganttApi.get).toHaveBeenCalledTimes(3)
  })

  it('shows an error when saving task edits fails', async () => {
    api.tasksApi.update.mockRejectedValueOnce(new Error('conflict'))
    const wrapper = await mountPage()

    await wrapper.find('.table-row-action').trigger('click')
    const drawer = wrapper.find('[data-test="task-drawer"]')
    await drawer.find('input[aria-label="Title"]').setValue('Refined API')
    await drawer.findAll('button').find((button) => button.text() === 'Save task')?.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Failed to update task.')
  })
})
