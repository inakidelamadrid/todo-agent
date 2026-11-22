export type PlaygroundGate = 'loading' | 'ready' | 'off' | 'not-admin' | 'error'

export type ProbeResult = { readonly ok: true } | { readonly ok: false; readonly status: number }

/** Pure: the playground answers 404 when switched off and 403 to anyone who is not an admin. */
export const gateFromProbe = (result: ProbeResult): PlaygroundGate => {
  if (result.ok) return 'ready'
  if (result.status === 404) return 'off'
  if (result.status === 403) return 'not-admin'
  return 'error'
}
