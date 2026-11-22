import { describe, expect, it, vi } from 'vitest'
import type { Me } from './session'
import { createSessionStore } from './useSessionStore'

const admin: Me = { userId: 'user_1', kind: 'user', roles: ['admin'] }

describe('useSessionStore', () => {
  it('sets ready and me after load', async () => {
    const store = createSessionStore(vi.fn().mockResolvedValue(admin))
    await store.getState().load()
    expect(store.getState()).toMatchObject({ me: admin, status: 'ready' })
  })

  it('leaves me null after a failed load', async () => {
    const store = createSessionStore(vi.fn().mockRejectedValue(new Error('boom')))
    await store.getState().load()
    expect(store.getState()).toMatchObject({ me: null, status: 'error' })
  })

  it('fetches once when loaded twice', async () => {
    const loadMe = vi.fn().mockResolvedValue(admin)
    const store = createSessionStore(loadMe)
    await Promise.all([store.getState().load(), store.getState().load()])
    await store.getState().load()
    expect(loadMe).toHaveBeenCalledTimes(1)
  })

  it('clears me on reset', async () => {
    const store = createSessionStore(vi.fn().mockResolvedValue(admin))
    await store.getState().load()
    store.getState().reset()
    expect(store.getState()).toMatchObject({ me: null, status: 'idle' })
  })
})
