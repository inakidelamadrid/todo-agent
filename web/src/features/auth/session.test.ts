import { describe, expect, it, vi } from 'vitest'
import { fetchMe, isAdmin, type Me, type Request } from './session'

const me = (roles: readonly string[]): Me => ({ userId: 'user_1', kind: 'user', roles })

describe('isAdmin', () => {
  it('is true with the admin role', () => {
    expect(isAdmin(me(['admin']))).toBe(true)
  })

  it('is false for null, empty or other roles', () => {
    expect(isAdmin(null)).toBe(false)
    expect(isAdmin(me([]))).toBe(false)
    expect(isAdmin(me(['viewer']))).toBe(false)
  })
})

describe('fetchMe', () => {
  it('parses roles and defaults them to empty', async () => {
    const withRoles = vi.fn().mockResolvedValue({ userId: 'user_1', kind: 'user', roles: ['admin'] })
    await expect(fetchMe(withRoles as unknown as Request)).resolves.toEqual(me(['admin']))
    expect(withRoles).toHaveBeenCalledWith('GET', '/me')

    const withoutRoles = vi.fn().mockResolvedValue({ userId: 'user_1', kind: 'user' })
    await expect(fetchMe(withoutRoles as unknown as Request)).resolves.toEqual(me([]))
  })
})
