import { type DateLabel, dateLabel, SIZE_LABEL } from './tasks'
import type { DateKey, Task, TaskContext } from './types'

export const CONTEXT_LABEL: Readonly<Record<TaskContext, string>> = {
  home: 'At home',
  computer: 'At the computer',
  phone: 'On the phone',
  errand: 'Out on an errand',
  anywhere: 'Anywhere',
}

export interface TaskRowView {
  readonly title: string
  readonly firstStep: string | null
  readonly sizeLabel: string
  readonly contextLabel: string
  readonly date: DateLabel | null
}

/** Pure: everything a task row shows, so the component only lays it out. */
export const taskRow = (task: Task, today: DateKey): TaskRowView => ({
  title: task.title,
  firstStep: task.firstStep.trim() || null,
  sizeLabel: SIZE_LABEL[task.size],
  contextLabel: CONTEXT_LABEL[task.context],
  date: dateLabel(task, today),
})
