import { describe, expect, it, vi } from 'vitest'
import { ApiError, type TasksApi } from '../api/client'
import { fixtureTasks } from '../fixtures'
import { removeTask, restoreTasks } from '../model/transitions'
import { createTasksStore } from './useTasksStore'

const tasks = fixtureTasks('2026-11-27')
const [first, second] = tasks

const fakeApi = (overrides: Partial<TasksApi> = {}): TasksApi =>
  ({
    listTasks: vi.fn(async () => tasks),
    completeTask: vi.fn(async (id: string) => ({ ...tasks.find((t) => t.id === id)!, status: 'done' as const })),
    dropTask: vi.fn(async (id: string) => ({ ...tasks.find((t) => t.id === id)!, status: 'dropped' as const })),
    reopenTask: vi.fn(async (id: string) => ({ ...tasks.find((t) => t.id === id)!, status: 'active' as const })),
    ...overrides,
  }) as unknown as TasksApi

const loaded = async (api: TasksApi) => {
  const store = createTasksStore(api)
  await store.getState().load()
  return store
}

const ids = (store: Awaited<ReturnType<typeof loaded>>) => store.getState().tasks.map((t) => t.id).sort()

describe('transitions', () => {
  it('remove and restore are pure', () => {
    const removed = removeTask(tasks, first.id)
    expect(removed).not.toContain(first)
    expect(tasks).toContain(first)
    expect(restoreTasks(removed, first)).toHaveLength(tasks.length)
    expect(restoreTasks(tasks, first)).toHaveLength(tasks.length)
  })
})

describe('useTasksStore', () => {
  it('load sets ready with tasks', async () => {
    const api = fakeApi()
    const store = await loaded(api)
    expect(store.getState()).toMatchObject({ status: 'ready', tasks, error: null })
    expect(api.listTasks).toHaveBeenCalledWith(['active'])
  })

  it('load exposes the error', async () => {
    const store = await loaded(fakeApi({ listTasks: vi.fn(async () => Promise.reject(new ApiError(0, 'down'))) }))
    expect(store.getState()).toMatchObject({ status: 'error', error: { status: 0, message: 'down' } })
  })

  it('complete removes optimistically and keeps it removed on success', async () => {
    const store = await loaded(fakeApi())
    const pending = store.getState().complete(first.id)
    expect(store.getState().tasks).not.toContainEqual(first)
    expect(store.getState().busyIds.has(first.id)).toBe(true)
    await pending
    expect(store.getState().tasks).not.toContainEqual(first)
    expect(store.getState().busyIds.size).toBe(0)
  })

  it('complete restores the task and exposes the error on failure', async () => {
    const store = await loaded(fakeApi({ completeTask: vi.fn(async () => Promise.reject(new ApiError(0, 'down'))) }))
    const before = ids(store)
    await expect(store.getState().complete(first.id)).rejects.toMatchObject({ status: 0 })
    expect(ids(store)).toEqual(before)
    expect(store.getState().tasks).toContainEqual(first)
  })

  it('drop then undo reopens the task', async () => {
    const api = fakeApi()
    const store = await loaded(api)
    await store.getState().drop(second.id)
    expect(store.getState().tasks).not.toContainEqual(second)
    await store.getState().reopen(second.id)
    expect(api.reopenTask).toHaveBeenCalledWith(second.id)
    expect(store.getState().tasks).toContainEqual(second)
  })

  it('ignores a second click while the first is in flight', async () => {
    const api = fakeApi()
    const store = await loaded(api)
    await Promise.all([store.getState().complete(first.id), store.getState().complete(first.id)])
    expect(api.completeTask).toHaveBeenCalledTimes(1)
  })
})
