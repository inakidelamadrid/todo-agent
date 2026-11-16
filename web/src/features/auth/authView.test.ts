import { describe, expect, it } from 'vitest'
import { resolveAuthView } from './authView'

describe('resolveAuthView', () => {
  it('is loading until Clerk has loaded', () => {
    expect(resolveAuthView({ isLoaded: false, isSignedIn: undefined, loadFailed: false })).toBe('loading')
  })

  it('lets a load failure win over everything', () => {
    expect(resolveAuthView({ isLoaded: false, isSignedIn: undefined, loadFailed: true })).toBe('error')
    expect(resolveAuthView({ isLoaded: true, isSignedIn: true, loadFailed: true })).toBe('error')
  })

  it('is signed-in when loaded and signed in', () => {
    expect(resolveAuthView({ isLoaded: true, isSignedIn: true, loadFailed: false })).toBe('signed-in')
  })

  it('is signed-out when loaded and not signed in', () => {
    expect(resolveAuthView({ isLoaded: true, isSignedIn: false, loadFailed: false })).toBe('signed-out')
    expect(resolveAuthView({ isLoaded: true, isSignedIn: undefined, loadFailed: false })).toBe('signed-out')
  })
})
