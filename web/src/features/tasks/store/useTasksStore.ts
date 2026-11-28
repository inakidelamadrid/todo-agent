import { create } from 'zustand'
import { type TasksApi, tasksApi } from '../api/client'
import { removeTask, restoreTasks } from '../model/transitions'
import type { Task } from '../model/types'

export type LoadStatus = 'idle' | 'loading' | 'ready' | 'error'

export interface LoadError {
  /** 0 = API unreachable, otherwise the HTTP status. */
  readonly status: number
  readonly message: string
}

export interface TasksState {
  readonly tasks: readonly Task[]
  readonly status: LoadStatus
  readonly error: LoadError | null
  readonly busyIds: ReadonlySet<string>
}

export interface TasksActions {
  readonly load: () => Promise<void>
  /** Optimistic; restores the task and rejects on failure. */
  readonly complete: (id: string) => Promise<void>
  /** Optimistic; restores the task and rejects on failure. */
  readonly drop: (id: string) => Promise<void>
  /** Undo for Done and Let go: waits for the server, then puts the task back. */
  readonly reopen: (id: string) => Promise<void>
}

const initial: TasksState = { tasks: [], status: 'idle', error: null, busyIds: new Set() }

const errorOf = (e: unknown): LoadError => ({
  status: typeof e === 'object' && e !== null && 'status' in e ? Number((e as { status: unknown }).status) : 0,
  message: e instanceof Error ? e.message : 'Something went wrong',
})

const withId = (ids: ReadonlySet<string>, id: string): ReadonlySet<string> => new Set([...ids, id])
const withoutId = (ids: ReadonlySet<string>, id: string): ReadonlySet<string> => new Set([...ids].filter((x) => x !== id))

/** Store factory with an injectable API, so actions are testable without a server. */
export const createTasksStore = (api: TasksApi) =>
  create<TasksState & TasksActions>()((set, get) => {
    /** Remove now, call the API, put the task back if it fails. */
    const optimisticRemove = (call: (id: string) => Promise<Task>) => async (id: string) => {
      const task = get().tasks.find((t) => t.id === id)
      if (!task || get().busyIds.has(id)) return
      set((s) => ({ tasks: removeTask(s.tasks, id), busyIds: withId(s.busyIds, id) }))
      try {
        await call(id)
      } catch (e) {
        set((s) => ({ tasks: restoreTasks(s.tasks, task) }))
        throw e
      } finally {
        set((s) => ({ busyIds: withoutId(s.busyIds, id) }))
      }
    }

    return {
      ...initial,

      load: async () => {
        set({ status: 'loading', error: null })
        try {
          set({ tasks: await api.listTasks(['active']), status: 'ready' })
        } catch (e) {
          set({ status: 'error', error: errorOf(e) })
        }
      },

      complete: optimisticRemove(api.completeTask),
      drop: optimisticRemove(api.dropTask),

      reopen: async (id) => {
        set((s) => ({ busyIds: withId(s.busyIds, id) }))
        try {
          const task = await api.reopenTask(id)
          set((s) => ({ tasks: restoreTasks(s.tasks, task) }))
        } finally {
          set((s) => ({ busyIds: withoutId(s.busyIds, id) }))
        }
      },
    }
  })

export const useTasksStore = createTasksStore(tasksApi)
