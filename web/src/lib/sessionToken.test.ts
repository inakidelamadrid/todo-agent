import { afterEach, describe, expect, it, vi } from 'vitest'
import { getSessionToken } from './sessionToken'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('getSessionToken', () => {
  it('returns the token from the current session', async () => {
    vi.stubGlobal('Clerk', { session: { getToken: async () => 'session-token-123' } })
    expect(await getSessionToken()).toBe('session-token-123')
  })

  it('returns null without a Clerk global', async () => {
    vi.stubGlobal('Clerk', undefined)
    expect(await getSessionToken()).toBeNull()
  })

  it('returns null without a session', async () => {
    vi.stubGlobal('Clerk', { session: null })
    expect(await getSessionToken()).toBeNull()

    vi.stubGlobal('Clerk', {})
    expect(await getSessionToken()).toBeNull()
  })

  it('does not cache between calls', async () => {
    const getToken = vi.fn().mockResolvedValueOnce('first-token').mockResolvedValueOnce('second-token')
    vi.stubGlobal('Clerk', { session: { getToken } })

    expect(await getSessionToken()).toBe('first-token')
    expect(await getSessionToken()).toBe('second-token')
    expect(getToken).toHaveBeenCalledTimes(2)
  })
})
