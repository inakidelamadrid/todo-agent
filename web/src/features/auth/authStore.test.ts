import { beforeEach, describe, expect, it } from 'vitest'
import { useAuthStore } from './authStore'

beforeEach(() => {
  useAuthStore.getState().reset()
})

describe('useAuthStore', () => {
  it('sets and resets the forbidden flag', () => {
    expect(useAuthStore.getState().forbidden).toBe(false)

    useAuthStore.getState().setForbidden()
    expect(useAuthStore.getState().forbidden).toBe(true)

    useAuthStore.getState().reset()
    expect(useAuthStore.getState().forbidden).toBe(false)
  })
})
