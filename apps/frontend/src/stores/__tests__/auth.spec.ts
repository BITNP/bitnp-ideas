import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '../auth'

const api = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}))

vi.mock('@/api/client', () => ({
  default: api,
}))

const user = {
  id: 'user-1',
  email: 'user@example.test',
  display_name: 'Test User',
  global_role: 'developer',
  is_active: true,
}

beforeEach(() => {
  localStorage.clear()
  api.get.mockReset()
  api.post.mockReset()
  setActivePinia(createPinia())
})

describe('auth store callback state handling', () => {
  it('rejects mismatched callback state before calling the backend', async () => {
    localStorage.setItem('auth_state', 'expected-state')
    const auth = useAuthStore()

    await expect(auth.handleCallback('code', 'wrong-state')).rejects.toThrow(
      'Invalid login state',
    )

    expect(api.get).not.toHaveBeenCalled()
    expect(localStorage.getItem('auth_state')).toBeNull()
  })

  it('stores the session and clears auth_state after a valid callback', async () => {
    localStorage.setItem('auth_state', 'expected-state')
    api.get.mockResolvedValue({
      data: { access_token: 'session-token', token_type: 'bearer', user },
    })
    const auth = useAuthStore()

    await auth.handleCallback('code', 'expected-state')

    expect(api.get).toHaveBeenCalledWith('/auth/callback', {
      params: expect.objectContaining({
        code: 'code',
        state: 'expected-state',
      }),
    })
    expect(auth.token).toBe('session-token')
    expect(auth.user).toEqual(user)
    expect(localStorage.getItem('auth_state')).toBeNull()
  })

  it('logs out through the backend and clears local session state', async () => {
    window.history.pushState({}, '', '/dashboard')
    localStorage.setItem('access_token', 'session-token')
    localStorage.setItem('user', JSON.stringify(user))
    localStorage.setItem('auth_state', 'stale-state')
    api.post.mockResolvedValue({ data: { message: 'logged out' } })
    const auth = useAuthStore()

    await auth.logout()

    expect(api.post).toHaveBeenCalledWith('/auth/logout')
    expect(auth.token).toBeNull()
    expect(auth.user).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
    expect(localStorage.getItem('auth_state')).toBeNull()
    expect(window.location.pathname).toBe('/login')
  })
})
