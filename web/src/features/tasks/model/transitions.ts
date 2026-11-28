import type { Task } from './types'

/** Pure: the list without that task. */
export const removeTask = (tasks: readonly Task[], id: string): readonly Task[] => tasks.filter((t) => t.id !== id)

/** Pure: put a task back (replacing any copy with the same id). */
export const restoreTasks = (tasks: readonly Task[], task: Task): readonly Task[] => [...removeTask(tasks, task.id), task]
