export type AuthView = 'loading' | 'error' | 'signed-out' | 'signed-in' | 'forbidden'

// Priority: a load failure wins, then loading, then forbidden when signed in, then the session.
export const resolveAuthView = (input: {
  readonly isLoaded: boolean
  readonly isSignedIn: boolean | undefined
  readonly loadFailed: boolean
  readonly forbidden?: boolean
}): AuthView => {
  if (input.loadFailed) return 'error'
  if (!input.isLoaded) return 'loading'
  if (!input.isSignedIn) return 'signed-out'
  return input.forbidden ? 'forbidden' : 'signed-in'
}
