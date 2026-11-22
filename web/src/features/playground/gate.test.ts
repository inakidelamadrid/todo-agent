import { describe, expect, it } from 'vitest'
import { gateFromProbe } from './gate'

describe('gateFromProbe', () => {
  it('is ready when the probe succeeds', () => {
    expect(gateFromProbe({ ok: true })).toBe('ready')
  })

  it('is off on 404', () => {
    expect(gateFromProbe({ ok: false, status: 404 })).toBe('off')
  })

  it('is not-admin on 403', () => {
    expect(gateFromProbe({ ok: false, status: 403 })).toBe('not-admin')
  })

  it('is error for other statuses and a network error', () => {
    for (const status of [0, 401, 500, 503]) {
      expect(gateFromProbe({ ok: false, status })).toBe('error')
    }
  })
})
