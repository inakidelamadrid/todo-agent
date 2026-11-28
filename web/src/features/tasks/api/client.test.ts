import { describe, expect, it, vi } from 'vitest'
import type { Task } from '../model/types'
import { createTasksApi, isApiError } from './client'

const task: Task = {
  id: 't1',
  title: 'Call dentist',
  notes: '',
  size: 'S',
  energy: 'medium',
  context: 'phone',
  doDate: '2026-11-27',
  dueDate: null,
  firstStep: 'Find the number',
  parentId: null,
  status: 'active',
  snoozedUntil: null,
}

const dto = { ...task, createdFrom: null, completedAt: null, droppedAt: null, createdAt: '2026-11-27T10:00:00Z', updatedAt: '2026-11-27T10:00:00Z' }

const json = (status: number, body: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

const setup = (response: Response) => {
  const fetchMock = vi.fn(async () => response)
  return { api: createTasksApi(fetchMock as unknown as typeof fetch, '/api', async () => 'tok'), fetchMock }
}

const call = (fetchMock: ReturnType<typeof vi.fn>) => {
  const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
  return {
    url,
    method: init.method,
    body: init.body ? JSON.parse(init.body as string) : undefined,
    headers: init.headers as Record<string, string>,
  }
}

describe('tasks client', () => {
  it('listTasks builds a repeated status query and strips server-only fields', async () => {
    const { api, fetchMock } = setup(json(200, [dto]))
    expect(await api.listTasks(['active', 'snoozed'])).toEqual([task])
    expect(call(fetchMock)).toMatchObject({ url: '/api/tasks?status=active&status=snoozed', method: 'GET' })
  })

  it('listTasks without statuses lets the server pick its default', async () => {
    const { api, fetchMock } = setup(json(200, []))
    await api.listTasks()
    expect(call(fetchMock).url).toBe('/api/tasks')
  })

  it('completeTask posts to /tasks/{id}/complete', async () => {
    const { api, fetchMock } = setup(json(200, { ...dto, status: 'done' }))
    expect((await api.completeTask('t1')).status).toBe('done')
    expect(call(fetchMock)).toMatchObject({ url: '/api/tasks/t1/complete', method: 'POST', body: undefined })
  })

  it.each([
    ['dropTask', '/api/tasks/t1/drop'],
    ['reopenTask', '/api/tasks/t1/reopen'],
  ] as const)('%s posts to %s', async (fn, url) => {
    const { api, fetchMock } = setup(json(200, dto))
    await api[fn]('t1')
    expect(call(fetchMock)).toMatchObject({ url, method: 'POST' })
  })

  it('snoozeTask sends {until}', async () => {
    const { api, fetchMock } = setup(json(200, { ...dto, status: 'snoozed', snoozedUntil: '2026-11-30' }))
    await api.snoozeTask('t1', '2026-11-30')
    expect(call(fetchMock)).toMatchObject({ url: '/api/tasks/t1/snooze', method: 'POST', body: { until: '2026-11-30' } })
  })

  it('creates, gets, updates and deletes', async () => {
    const created = setup(json(201, dto))
    await created.api.createTask({ title: 'Call dentist', size: 'S' })
    expect(call(created.fetchMock)).toMatchObject({ url: '/api/tasks', method: 'POST', body: { title: 'Call dentist', size: 'S' } })

    const got = setup(json(200, dto))
    await got.api.getTask('t1')
    expect(call(got.fetchMock)).toMatchObject({ url: '/api/tasks/t1', method: 'GET' })

    const patched = setup(json(200, dto))
    await patched.api.updateTask('t1', { title: 'Call the dentist' })
    expect(call(patched.fetchMock)).toMatchObject({ url: '/api/tasks/t1', method: 'PATCH', body: { title: 'Call the dentist' } })

    const deleted = setup(json(204, undefined))
    await deleted.api.deleteTask('t1')
    expect(call(deleted.fetchMock)).toMatchObject({ url: '/api/tasks/t1', method: 'DELETE' })
  })

  it('409 becomes an ApiError with status 409', async () => {
    const { api } = setup(json(409, { detail: "Can't complete a task that is done" }))
    const error = await api.completeTask('t1').catch((e: unknown) => e)
    expect(isApiError(error) && error.status).toBe(409)
  })

  it('sends the bearer token', async () => {
    const { api, fetchMock } = setup(json(200, []))
    await api.listTasks()
    expect(call(fetchMock).headers.Authorization).toBe('Bearer tok')
  })
})
