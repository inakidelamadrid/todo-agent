import { describe, expect, it } from 'vitest'
import { resolveScreen } from './screen'

describe('resolveScreen', () => {
  it('shows the playground to an admin at #playground', () => {
    expect(resolveScreen('#playground', true)).toBe('playground')
  })

  it('shows Bills to a non-admin at #playground', () => {
    expect(resolveScreen('#playground', false)).toBe('bills')
  })

  it('shows Bills for empty, #bills and unknown hashes', () => {
    for (const hash of ['', '#bills', '#nope', '#Playground', '#playground/x']) {
      expect(resolveScreen(hash, true)).toBe('bills')
    }
  })
})
