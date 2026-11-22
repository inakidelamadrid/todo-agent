import { create } from 'zustand'
import { createRequest } from '@/lib/api'
import { getSessionToken } from '@/lib/sessionToken'
import { handleAuthFailure } from './authFailure'
import { fetchMe, type Me } from './session'

export type SessionStatus = 'idle' | 'loading' | 'ready' | 'error'

export interface SessionState {
  readonly me: Me | null
  readonly status: SessionStatus
  /** Loads `/me` once; a no-op while loading or ready. */
  readonly load: () => Promise<void>
  readonly reset: () => void
}

/** Store factory with an injectable loader, so it is testable without a server. */
export const createSessionStore = (loadMe: () => Promise<Me>) =>
  create<SessionState>()((set, get) => ({
    me: null,
    status: 'idle',

    load: async () => {
      if (get().status === 'loading' || get().status === 'ready') return
      set({ status: 'loading' })
      try {
        set({ me: await loadMe(), status: 'ready' })
      } catch {
        set({ me: null, status: 'error' })
      }
    },

    reset: () => set({ me: null, status: 'idle' }),
  }))

const request = createRequest((...args) => fetch(...args), '/api', getSessionToken, handleAuthFailure)

export const useSessionStore = createSessionStore(() => fetchMe(request))
