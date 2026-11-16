import { create } from 'zustand'

export interface AuthState {
  readonly forbidden: boolean
  readonly setForbidden: () => void
  readonly reset: () => void
}

export const useAuthStore = create<AuthState>()((set) => ({
  forbidden: false,
  setForbidden: () => set({ forbidden: true }),
  reset: () => set({ forbidden: false }),
}))
