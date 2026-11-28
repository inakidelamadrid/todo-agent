import type { DateKey, Task } from './model/types'

const addDays = (date: DateKey, n: number): DateKey => {
  const [y, m, d] = date.split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d + n)).toISOString().slice(0, 10)
}

const task = (id: string, title: string, extra: Partial<Task>): Task => ({
  id,
  title,
  notes: '',
  size: 'S',
  energy: 'medium',
  context: 'anywhere',
  doDate: null,
  dueDate: null,
  firstStep: '',
  parentId: null,
  status: 'active',
  snoozedUntil: null,
  ...extra,
})

/** Dev-only sample list relative to `today`: every group, a past-its-date task, a long title, no first step. */
export const fixtureTasks = (today: DateKey): readonly Task[] => [
  task('f1', 'Call the dentist about the cleaning', { context: 'phone', doDate: today, firstStep: 'Find the number on the last invoice' }),
  task('f2', 'Renew the car registration', { context: 'computer', size: 'M', dueDate: addDays(today, -3), firstStep: 'Open the state portal' }),
  task('f3', 'Buy cat food', { context: 'errand', size: 'XS', doDate: today }),
  task('f4', 'Send the quarterly invoice to the client', { context: 'computer', size: 'M', doDate: addDays(today, 2), dueDate: addDays(today, 4), firstStep: 'Export last month’s hours' }),
  task('f5', 'Plan the garden beds for spring, including the compost corner and the new drip irrigation line', { context: 'home', size: 'XL', doDate: addDays(today, 12) }),
  task('f6', 'Read the lease renewal', { context: 'home', size: 'L', firstStep: 'Print it' }),
  task('f7', 'Back up the photo library', { context: 'anywhere', size: 'S' }),
]
