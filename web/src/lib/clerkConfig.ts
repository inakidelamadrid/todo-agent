const PUBLISHABLE_PREFIXES = ['pk_test_', 'pk_live_'] as const

// Only a publishable key may reach the bundle; a secret key (`sk_…`) or anything else is refused.
export const readPublishableKey = (env: { readonly VITE_CLERK_PUBLISHABLE_KEY?: unknown }): string | null => {
  const value = env.VITE_CLERK_PUBLISHABLE_KEY
  if (typeof value !== 'string') return null
  const key = value.trim()
  return PUBLISHABLE_PREFIXES.some((prefix) => key.startsWith(prefix)) ? key : null
}
