import { toast } from 'sonner'
import { useAuthStore } from './authStore'

export type AuthFailure = 'session-ended' | 'forbidden'

interface ClerkGlobal {
  readonly Clerk?: {
    readonly signOut?: () => Promise<void>
  } | null
}

/** Pure classifier mapping an HTTP status code to an auth failure kind. */
export const describeAuthFailure = (status: number): AuthFailure | null =>
  status === 401 ? 'session-ended' : status === 403 ? 'forbidden' : null

const effects: Readonly<Record<AuthFailure, () => void>> = {
  'session-ended': () => {
    void (globalThis as ClerkGlobal).Clerk?.signOut?.()?.catch(() => undefined)
    toast('Your session ended. Please sign in again.', { id: 'session-ended' })
  },
  forbidden: () => {
    useAuthStore.getState().setForbidden()
  },
}

export const handleAuthFailure = (status: number): void => {
  const failure = describeAuthFailure(status)
  if (failure) effects[failure]()
}
