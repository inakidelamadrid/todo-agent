import { describe, expect, it } from 'vitest'
import { accountLabel } from './accountLabel'

describe('accountLabel', () => {
  it('prefers full name', () => {
    expect(accountLabel({ fullName: 'Ignacio', primaryEmail: 'ignacio@example.com' })).toBe('Ignacio')
  })

  it('falls back to email', () => {
    expect(accountLabel({ fullName: null, primaryEmail: 'ignacio@example.com' })).toBe('ignacio@example.com')
    expect(accountLabel({ fullName: '', primaryEmail: 'ignacio@example.com' })).toBe('ignacio@example.com')
  })

  it('falls back to Account for null, undefined and blank values', () => {
    expect(accountLabel(null)).toBe('Account')
    expect(accountLabel(undefined)).toBe('Account')
    expect(accountLabel({})).toBe('Account')
    expect(accountLabel({ fullName: '   ', primaryEmail: '  ' })).toBe('Account')
  })

  it('trims whitespace', () => {
    expect(accountLabel({ fullName: '  Ignacio  ', primaryEmail: 'ignacio@example.com' })).toBe('Ignacio')
    expect(accountLabel({ fullName: '   ', primaryEmail: '  ignacio@example.com  ' })).toBe('ignacio@example.com')
  })
})
