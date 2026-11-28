import { daysBetween } from '@/features/bills/model/schedule'
import type { DateKey, Task, TaskSize } from './types'

export const SIZE_LABEL: Readonly<Record<TaskSize, string>> = {
  XS: 'XS · 5 min',
  S: 'S · 15 min',
  M: 'M · 45 min',
  L: 'L · 2 h',
  XL: 'XL · break it down',
}

export interface DateLabel {
  readonly text: string
  /** Past dates are muted, never a warning colour. */
  readonly tone: 'muted' | 'normal'
}

const utcDate = (date: DateKey): Date => {
  const [y, m, d] = date.split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d))
}

const weekday = (date: DateKey): string =>
  new Intl.DateTimeFormat('en-US', { weekday: 'short', timeZone: 'UTC' }).format(utcDate(date))

const dayMonth = (date: DateKey): string =>
  new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' }).format(utcDate(date))

const when = (date: DateKey, today: DateKey): string => {
  const days = daysBetween(today, date)
  if (days === 0) return 'today'
  if (days === 1) return 'tomorrow'
  return days <= 6 ? weekday(date) : dayMonth(date)
}

/** Pure: calm wording for a task's date; the due date wins over the do date. */
export const dateLabel = (task: Pick<Task, 'doDate' | 'dueDate'>, today: DateKey): DateLabel | null => {
  const date = task.dueDate ?? task.doDate
  if (date === null) return null
  if (date < today) return { text: 'Past its date', tone: 'muted' }
  const prefix = task.dueDate ? 'Due' : 'Planned for'
  return { text: `${prefix} ${when(date, today)}`, tone: 'normal' }
}

export type GroupKey = 'today' | 'upcoming' | 'anytime'

export interface TaskGroup {
  readonly key: GroupKey
  readonly label: string
  readonly tasks: readonly Task[]
}

const GROUPS: readonly { readonly key: GroupKey; readonly label: string }[] = [
  { key: 'today', label: 'Today' },
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'anytime', label: 'Anytime' },
]

const groupOf = (task: Task, today: DateKey): GroupKey => {
  if ((task.doDate !== null && task.doDate <= today) || (task.dueDate !== null && task.dueDate <= today)) return 'today'
  return task.doDate !== null || task.dueDate !== null ? 'upcoming' : 'anytime'
}

/** Earlier due date first (no due date last), then title. */
const byDueThenTitle = (a: Task, b: Task): number =>
  (a.dueDate ?? '9999-99-99').localeCompare(b.dueDate ?? '9999-99-99') || a.title.localeCompare(b.title)

/** Pure: today / upcoming / anytime, empty groups omitted. */
export const groupByDoDate = (tasks: readonly Task[], today: DateKey): readonly TaskGroup[] =>
  GROUPS.map(({ key, label }) => ({
    key,
    label,
    tasks: tasks.filter((t) => groupOf(t, today) === key).toSorted(byDueThenTitle),
  })).filter((g) => g.tasks.length > 0)
