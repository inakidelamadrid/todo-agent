import { describe, expect, it } from 'vitest'
import { formatReceivedAt, statusTone } from './updateLog'

describe('statusTone', () => {
  it('maps processed to good, failed to bad and received to neutral', () => {
    expect(statusTone('processed')).toBe('good')
    expect(statusTone('failed')).toBe('bad')
    expect(statusTone('received')).toBe('neutral')
  })
})

describe('formatReceivedAt', () => {
  const now = new Date('2026-11-22T20:30:00Z')

  it('is relative within the hour and absolute after it', () => {
    expect(formatReceivedAt('2026-11-22T20:29:40Z', now)).toBe('just now')
    expect(formatReceivedAt('2026-11-22T20:31:00Z', now)).toBe('just now')
    expect(formatReceivedAt('2026-11-22T20:25:00Z', now)).toBe('5 min ago')
    expect(formatReceivedAt('2026-11-22T19:31:00Z', now)).toBe('59 min ago')
    expect(formatReceivedAt('2026-11-22T19:30:00Z', now)).toBe('Nov 22, 13:30')
  })

  it('uses Mexico City time for absolute times', () => {
    // 03:15 UTC on the 21st is still the evening of the 20th in Mexico City (UTC-6).
    expect(formatReceivedAt('2026-11-21T03:15:00Z', now)).toBe('Nov 20, 21:15')
  })
})
