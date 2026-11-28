import { handleAuthFailure } from '@/features/auth/authFailure'
import { createRequest, type Fetch, type GetToken } from '@/lib/api'
import { getSessionToken } from '@/lib/sessionToken'
import type { DateKey, Task, TaskStatus } from '../model/types'

export { ApiError, isApiError } from '@/lib/api'

/** Fields the server accepts on create; everything but the title has a server default. */
export type TaskInput = Pick<Task, 'title'> &
  Partial<Pick<Task, 'notes' | 'size' | 'energy' | 'context' | 'doDate' | 'dueDate' | 'firstStep' | 'parentId'>>

/** Shape the API returns: a Task plus server-only fields. */
interface TaskDto extends Task {
  readonly createdFrom?: string | null
  readonly completedAt?: string | null
  readonly droppedAt?: string | null
  readonly createdAt?: string
  readonly updatedAt?: string
}

/** Pure: strip server-only fields so the store keeps the shared domain shape. */
export const toTask = ({
  id,
  title,
  notes,
  size,
  energy,
  context,
  doDate,
  dueDate,
  firstStep,
  parentId,
  status,
  snoozedUntil,
}: TaskDto): Task => ({ id, title, notes, size, energy, context, doDate, dueDate, firstStep, parentId, status, snoozedUntil })

const statusQuery = (statuses: readonly TaskStatus[] = []): string =>
  statuses.length ? `?${statuses.map((s) => `status=${encodeURIComponent(s)}`).join('&')}` : ''

/** Build the client around an injectable fetch (tests pass a mock). */
export const createTasksApi = (
  fetchImpl: Fetch = (...args) => fetch(...args),
  base = '/api',
  getToken: GetToken = getSessionToken,
) => {
  const request = createRequest(fetchImpl, base, getToken, handleAuthFailure)
  const one = async (method: string, path: string, body?: unknown): Promise<Task> => toTask(await request<TaskDto>(method, path, body))
  const action = (verb: 'complete' | 'drop' | 'reopen') => (id: string) => one('POST', `/tasks/${id}/${verb}`)

  return {
    listTasks: async (statuses?: readonly TaskStatus[]): Promise<readonly Task[]> =>
      (await request<readonly TaskDto[]>('GET', `/tasks${statusQuery(statuses)}`)).map(toTask),
    getTask: (id: string) => one('GET', `/tasks/${id}`),
    createTask: (input: TaskInput) => one('POST', '/tasks', input),
    updateTask: (id: string, patch: Partial<TaskInput>) => one('PATCH', `/tasks/${id}`, patch),
    deleteTask: (id: string): Promise<void> => request<void>('DELETE', `/tasks/${id}`),
    completeTask: action('complete'),
    dropTask: action('drop'),
    reopenTask: action('reopen'),
    snoozeTask: (id: string, until: DateKey) => one('POST', `/tasks/${id}/snooze`, { until }),
  }
}

export type TasksApi = ReturnType<typeof createTasksApi>

export const tasksApi: TasksApi = createTasksApi()
