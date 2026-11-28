import type { DateKey } from '@/features/bills/model/types'

export type { DateKey }

export type TaskSize = 'XS' | 'S' | 'M' | 'L' | 'XL'
export type Energy = 'low' | 'medium' | 'high'
export type TaskContext = 'home' | 'computer' | 'phone' | 'errand' | 'anywhere'
export type TaskStatus = 'active' | 'snoozed' | 'done' | 'dropped'

/** Mirrors `TaskOut` in `api/app/tasks/schemas.py`, minus server-only fields. */
export interface Task {
  readonly id: string
  readonly title: string
  readonly notes: string
  readonly size: TaskSize
  readonly energy: Energy
  readonly context: TaskContext
  readonly doDate: DateKey | null
  readonly dueDate: DateKey | null
  readonly firstStep: string
  readonly parentId: string | null
  readonly status: TaskStatus
  readonly snoozedUntil: DateKey | null
}
