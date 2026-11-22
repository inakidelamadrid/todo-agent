import type { UpdateLogFilters, UpdateLogItem } from './updateLog'

const minutesAgo = (now: Date, minutes: number) => new Date(now.getTime() - minutes * 60_000).toISOString()

/** Sample rows for the Updates tab until FE-024 wires it to the API. */
export const sampleUpdates = (now: Date): readonly UpdateLogItem[] => [
  { updateId: 900_112, kind: 'command', route: 'command:help', status: 'processed', receivedAt: minutesAgo(now, 0), playground: false },
  { updateId: -12, kind: 'text', route: 'default', status: 'processed', receivedAt: minutesAgo(now, 4), playground: true },
  { updateId: 900_111, kind: 'callback', route: 'callback:bills.mark_paid', status: 'failed', receivedAt: minutesAgo(now, 18), playground: false },
  { updateId: 900_110, kind: 'voice', route: 'default', status: 'received', receivedAt: minutesAgo(now, 42), playground: false },
  { updateId: 900_109, kind: 'photo', route: 'keyword:vault', status: 'processed', receivedAt: minutesAgo(now, 95), playground: false },
  { updateId: 900_108, kind: 'command', route: 'command:pause', status: 'processed', receivedAt: minutesAgo(now, 60 * 26), playground: false },
]

/** Fixture-only filtering; the real filters run on the server. */
export const filterSample = (items: readonly UpdateLogItem[], filters: UpdateLogFilters): readonly UpdateLogItem[] =>
  items.filter(
    (i) =>
      (filters.status === 'all' || i.status === filters.status) &&
      i.route.toLowerCase().includes(filters.route.trim().toLowerCase()),
  )
