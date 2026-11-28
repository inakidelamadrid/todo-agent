import { describe, expect, it } from 'vitest'
import { resolveScreen, type ScreenDef, visibleNav } from './screen'

const def = (id: string, extra: Partial<ScreenDef> = {}): ScreenDef => ({ id, label: id, icon: null, render: () => null, ...extra })

const defs: readonly ScreenDef[] = [def('bills'), def('playground', { adminOnly: true }), def('dev-x', { devOnly: true })]

const admin = { isAdmin: true, isDev: false }
const member = { isAdmin: false, isDev: false }

describe('resolveScreen', () => {
  it('shows the playground to an admin at #playground', () => {
    expect(resolveScreen('#playground', defs, admin).id).toBe('playground')
  })

  it('hides admin screens from non-admins', () => {
    expect(resolveScreen('#playground', defs, member).id).toBe('bills')
    expect(visibleNav(defs, member, 'bills').map((n) => n.href)).toEqual(['#bills'])
  })

  it('unknown hash falls back to bills', () => {
    for (const hash of ['', '#bills', '#nope', '#Playground', '#playground/x']) {
      expect(resolveScreen(hash, defs, admin).id).toBe('bills')
    }
  })

  it('dev-only screens resolve only in dev and never appear in nav', () => {
    expect(resolveScreen('#dev-x', defs, admin).id).toBe('bills')
    expect(resolveScreen('#dev-x', defs, { ...admin, isDev: true }).id).toBe('dev-x')
    expect(visibleNav(defs, { isAdmin: true, isDev: true }, 'dev-x').map((n) => n.href)).toEqual(['#bills', '#playground'])
  })
})

describe('visibleNav', () => {
  it('marks the current screen', () => {
    expect(visibleNav(defs, admin, 'playground').map((n) => n.current)).toEqual([false, true])
  })
})
