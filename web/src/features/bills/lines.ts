import type { Line, Recurrence, Status } from './model/types'

export const LINE_META: Readonly<Record<Line, { readonly label: string; readonly color: string }>> = {
  utilities: { label: 'Utilities', color: 'var(--line-utilities)' },
  telecom: { label: 'Internet & phone', color: 'var(--line-telecom)' },
  streaming: { label: 'Streaming', color: 'var(--line-streaming)' },
  software: { label: 'Software & cloud', color: 'var(--line-software)' },
}

export const STATUS_LABEL: Readonly<Record<Status, string>> = {
  overdue: 'Overdue',
  'due-soon': 'Due soon',
  upcoming: 'Upcoming',
  paid: 'Paid',
}

export const RECURRENCE_LABEL: Readonly<Record<Recurrence, string>> = {
  monthly: 'Every month',
  bimonthly: 'Every 2 months',
  yearly: 'Every year',
}
