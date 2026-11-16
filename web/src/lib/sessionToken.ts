import type { GetToken } from './api'

interface ClerkGlobal {
  readonly Clerk?: {
    readonly session?: {
      readonly getToken: () => Promise<string | null>
    } | null
  } | null
}

/** Read a fresh session token from Clerk's browser global, or `null` when unavailable. */
export const getSessionToken: GetToken = async () =>
  (await (globalThis as ClerkGlobal).Clerk?.session?.getToken()) ?? null
