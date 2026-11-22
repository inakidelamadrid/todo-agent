import { handleAuthFailure } from '@/features/auth/authFailure'
import { createRequest, type Fetch, type OnAuthFailure } from '@/lib/api'
import { getSessionToken } from '@/lib/sessionToken'

/**
 * Forward only 401 (the session ended) to the app-wide handler. A 403 from a playground
 * endpoint means 'not an admin' for this area; it must not flip the whole app to not-allowed.
 */
export const forwardUnauthorizedOnly =
  (handle: OnAuthFailure): OnAuthFailure =>
  (status) => {
    if (status === 401) handle(status)
  }

export const createPlaygroundRequest = (fetchImpl: Fetch = (...args) => fetch(...args), base = '/api') =>
  createRequest(fetchImpl, base, getSessionToken, forwardUnauthorizedOnly(handleAuthFailure))
