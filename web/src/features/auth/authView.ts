export type AuthView = 'loading' | 'error' | 'signed-out' | 'signed-in'

// Priority: a load failure wins, then loading, then the session.
export const resolveAuthView = (input: {
  readonly isLoaded: boolean
  readonly isSignedIn: boolean | undefined
  readonly loadFailed: boolean
}): AuthView => {
  if (input.loadFailed) return 'error'
  if (!input.isLoaded) return 'loading'
  return input.isSignedIn ? 'signed-in' : 'signed-out'
}
