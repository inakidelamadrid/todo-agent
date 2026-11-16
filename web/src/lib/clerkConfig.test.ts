import { describe, expect, it } from 'vitest'
import { readPublishableKey } from './clerkConfig'

const read = (value: unknown) => readPublishableKey({ VITE_CLERK_PUBLISHABLE_KEY: value })

describe('readPublishableKey', () => {
  it('reads a test key', () => {
    expect(read('pk_test_abc')).toBe('pk_test_abc')
  })

  it('reads a live key', () => {
    expect(read('pk_live_abc')).toBe('pk_live_abc')
  })

  it('trims whitespace', () => {
    expect(read('  pk_test_abc\n')).toBe('pk_test_abc')
  })

  it('returns null for undefined, blank and non-string values', () => {
    expect(readPublishableKey({})).toBeNull()
    expect(read('')).toBeNull()
    expect(read('   ')).toBeNull()
    expect(read(42)).toBeNull()
  })

  it('refuses a secret key', () => {
    expect(read('sk_test_abc')).toBeNull()
  })

  it('refuses other text', () => {
    expect(read('hello')).toBeNull()
  })
})
