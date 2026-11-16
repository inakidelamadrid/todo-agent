import { afterEach, describe, expect, it, vi } from 'vitest'
import { toast } from 'sonner'
import { describeAuthFailure, handleAuthFailure } from './authFailure'

vi.mock('sonner', () => ({
  toast: vi.fn(),
}))

afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

describe('describeAuthFailure', () => {
  it('classifies 401 as session-ended', () => {
    expect(describeAuthFailure(401)).toBe('session-ended')
  })

  it('classifies 403 as forbidden', () => {
    expect(describeAuthFailure(403)).toBe('forbidden')
  })

  it('returns null for other statuses', () => {
    expect(describeAuthFailure(400)).toBeNull()
    expect(describeAuthFailure(404)).toBeNull()
    expect(describeAuthFailure(500)).toBeNull()
    expect(describeAuthFailure(200)).toBeNull()
  })
})

describe('handleAuthFailure', () => {
  it('signs out and shows a deduplicated toast on 401', () => {
    const signOut = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('Clerk', { signOut })

    handleAuthFailure(401)

    expect(signOut).toHaveBeenCalledTimes(1)
    expect(toast).toHaveBeenCalledWith('Your session ended. Please sign in again.', { id: 'session-ended' })
  })

  it('does nothing yet on 403 or other statuses', () => {
    const signOut = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('Clerk', { signOut })

    handleAuthFailure(403)
    handleAuthFailure(500)

    expect(signOut).not.toHaveBeenCalled()
    expect(toast).not.toHaveBeenCalled()
  })
})
