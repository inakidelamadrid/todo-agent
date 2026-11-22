import { useSyncExternalStore } from 'react'

export type Screen = 'bills' | 'playground'

/** Pure: only an admin reaches the playground; every other hash is Bills. */
export const resolveScreen = (hash: string, isAdmin: boolean): Screen =>
  hash === '#playground' && isAdmin ? 'playground' : 'bills'

const subscribe = (onChange: () => void) => {
  window.addEventListener('hashchange', onChange)
  return () => window.removeEventListener('hashchange', onChange)
}

const readHash = () => window.location.hash

/** The one side effect: follow `hashchange`, so links and Back/Forward switch screens. */
export const useHashScreen = (isAdmin: boolean): Screen => resolveScreen(useSyncExternalStore(subscribe, readHash), isAdmin)
