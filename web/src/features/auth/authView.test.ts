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

  it('is forbidden when signed in and forbidden', () => {
    expect(resolveAuthView({ isLoaded: true, isSignedIn: true, loadFailed: false, forbidden: true })).toBe('forbidden')
  })

  it('ignores the forbidden flag when signed out', () => {
    expect(resolveAuthView({ isLoaded: true, isSignedIn: false, loadFailed: false, forbidden: true })).toBe('signed-out')
    expect(resolveAuthView({ isLoaded: true, isSignedIn: undefined, loadFailed: false, forbidden: true })).toBe('signed-out')
  })

  it('lets error and loading still take priority over forbidden', () => {
    expect(resolveAuthView({ isLoaded: true, isSignedIn: true, loadFailed: true, forbidden: true })).toBe('error')
    expect(resolveAuthView({ isLoaded: false, isSignedIn: true, loadFailed: false, forbidden: true })).toBe('loading')
  })
})
