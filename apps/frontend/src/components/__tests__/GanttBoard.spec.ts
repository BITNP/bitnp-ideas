/* eslint-disable vue/one-component-per-file, vue/require-prop-types */
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import EmptyState from '../EmptyState.vue'
import GanttBoard from '../GanttBoard.vue'

vi.mock('@/api/modules', () => ({
  ganttApi: {
    bulkUpdate: vi.fn(),
    addDependency: vi.fn(),
    removeDependency: vi.fn(),
  },
}))

vi.mock('jordium-gantt-vue3', () => ({
  GanttChart: defineComponent({
    props: ['timeScale', 'tasks'],
    template: '<div data-test="gantt-chart" :data-scale="timeScale">{{ tasks.length }}</div>',
  }),
  TaskListColumn: defineComponent({
    template: '<div />',
  }),
}))

const task = {
  id: 'task-1',
  project_id: 'project-1',
  title: 'Design API',
  description: 'Shape the endpoints.',
  status: 'todo',
  assignee: { id: 'user-1', name: 'Developer' },
  start_date: '2026-07-01',
  end_date: '2026-07-03',
  progress: 20,
  version: 1,
  created_at: '2026-06-01T00:00:00Z',
  updated_at: '2026-06-02T00:00:00Z',
}

const passthroughStub = defineComponent({
  props: ['title'],
  template: '<div><slot /></div>',
})

const buttonStub = defineComponent({
  props: ['value'],
  emits: ['click'],
  template: '<button :data-value="value" @click="$emit(\'click\', $event)"><slot /></button>',
})

const buttonToggleStub = defineComponent({
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: '<div data-test="scale-toggle"><slot /></div>',
})

function mountBoard(props = {}) {
  return mount(GanttBoard, {
    props: {
      tasks: [task],
      dependencies: [],
      projectId: 'project-1',
      ...props,
    },
    global: {
      stubs: {
        VAvatar: passthroughStub,
        VBtn: buttonStub,
        VBtnToggle: buttonToggleStub,
        VCard: passthroughStub,
        VCardText: passthroughStub,
        VCardTitle: passthroughStub,
        VChip: passthroughStub,
        VDivider: passthroughStub,
        VIcon: passthroughStub,
        'v-avatar': passthroughStub,
        'v-btn': buttonStub,
        'v-btn-toggle': buttonToggleStub,
        'v-card': passthroughStub,
        'v-card-text': passthroughStub,
        'v-card-title': passthroughStub,
        'v-chip': passthroughStub,
        'v-divider': passthroughStub,
        'v-icon': passthroughStub,
      },
    },
  })
}

describe('GanttBoard', () => {
  it('uses week scale by default and lets the toolbar switch to day scale', async () => {
    const wrapper = mountBoard()

    expect(wrapper.find('[data-test="gantt-chart"]').attributes('data-scale')).toBe('week')

    await wrapper.findComponent(buttonToggleStub).vm.$emit('update:modelValue', 'day')

    expect(wrapper.find('[data-test="gantt-chart"]').attributes('data-scale')).toBe('day')
  })

  it('uses month scale for compact snapshots', () => {
    const wrapper = mountBoard({ compact: true, readonly: true })

    expect(wrapper.find('[data-test="gantt-chart"]').attributes('data-scale')).toBe('month')
    expect(wrapper.find('[data-test="scale-toggle"]').exists()).toBe(false)
  })

  it('summarizes plan health above the chart', () => {
    const wrapper = mountBoard({
      dependencies: [{
        id: 'dependency-1',
        predecessor_task_id: 'task-1',
        successor_task_id: 'task-2',
        dependency_type: 'finish_to_start',
      }],
    })

    const summaryText = wrapper.find('[data-test="gantt-summary"]').text()
    expect(summaryText).toContain('Tasks 1')
    expect(summaryText).toContain('Scheduled 1')
    expect(summaryText).toContain('Dependencies 1')
  })

  it('offers task creation from the empty editable plan state', async () => {
    const wrapper = mountBoard({
      tasks: [],
      showCreateTaskAction: true,
    })

    expect(wrapper.text()).toContain('No scheduled tasks yet')

    wrapper.findComponent(EmptyState).vm.$emit('action')

    const emitted = wrapper.emitted('createTask') ?? wrapper.emitted('create-task')
    expect(emitted).toHaveLength(1)
  })
})
