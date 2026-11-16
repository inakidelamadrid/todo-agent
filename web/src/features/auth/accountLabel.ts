export interface AccountUser {
  readonly fullName?: string | null
  readonly primaryEmail?: string | null
}

/** Prefer the user's trimmed full name, then primary email, then a neutral fallback. */
export const accountLabel = (user: AccountUser | null | undefined): string =>
  user?.fullName?.trim() || user?.primaryEmail?.trim() || 'Account'
