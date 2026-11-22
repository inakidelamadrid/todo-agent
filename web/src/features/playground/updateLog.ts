import type { UpdateStatus } from './types'

export type { UpdateLogItem, UpdateStatus } from './types'

export interface UpdateLogFilters {
  readonly status: UpdateStatus | 'all'
  readonly route: string
}

export type Tone = 'neutral' | 'good' | 'bad'

const TONES: Readonly<Record<UpdateStatus, Tone>> = { received: 'neutral', processed: 'good', failed: 'bad' }

export const statusTone = (status: UpdateStatus): Tone => TONES[status]

const absolute = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
  timeZone: 'America/Mexico_City',
})

/** Pure: 'just now', then 'N min ago' within the hour, then a date and time in Mexico City. */
export const formatReceivedAt = (iso: string, now: Date): string => {
  const minutes = Math.floor((now.getTime() - new Date(iso).getTime()) / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  return absolute.format(new Date(iso))
}
