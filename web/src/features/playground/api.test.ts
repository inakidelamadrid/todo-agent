import { describe, expect, it, vi } from 'vitest'
import { ApiError, createRequest } from '@/lib/api'
import { createPlaygroundApi, updatesQuery } from './api'
import { forwardUnauthorizedOnly } from './request'

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

const setup = (response: Response | Error) => {
  const fetchMock = vi.fn(async () => {
    if (response instanceof Error) throw response
    return response
  })
  const onAuthFailure = vi.fn()
  const request = createRequest(fetchMock as unknown as typeof fetch, '/api', undefined, forwardUnauthorizedOnly(onAuthFailure))
  return { api: createPlaygroundApi(request), fetchMock, onAuthFailure }
}

const call = (fetchMock: ReturnType<typeof vi.fn>) => {
  const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
  return { url, method: init.method, body: init.body ? JSON.parse(init.body as string) : undefined }
}

describe('playground read client (FE-021)', () => {
  it('probes: 200 is ok; 404, 403 and network errors carry their status', async () => {
    expect(await setup(json(200, { enabled: true })).api.probe()).toEqual({ ok: true })
    expect(await setup(json(404, { detail: 'Not found' })).api.probe()).toEqual({ ok: false, status: 404 })
    expect(await setup(json(403, { detail: 'Forbidden' })).api.probe()).toEqual({ ok: false, status: 403 })
    expect(await setup(new TypeError('offline')).api.probe()).toEqual({ ok: false, status: 0 })
    const { api, fetchMock } = setup(json(200, { enabled: true }))
    await api.probe()
    expect(call(fetchMock)).toMatchObject({ url: '/api/admin/telegram/playground', method: 'GET' })
  })

  it('lists updates with only the filters that are set as query parameters', async () => {
    const item = { updateId: 1, kind: 'command', route: 'core.help', status: 'processed', receivedAt: '2026-11-16T15:04:05Z', playground: false }
    const { api, fetchMock } = setup(json(200, { items: [item] }))
    expect(await api.listUpdates({ limit: 50, status: 'failed', route: 'core help' })).toEqual([item])
    expect(call(fetchMock).url).toBe('/api/admin/telegram/updates?limit=50&status=failed&route=core+help')
    expect(updatesQuery()).toBe('')
    expect(updatesQuery({ status: undefined, route: '' })).toBe('')
  })

  it('lists templates', async () => {
    const templates = [{ name: 'help', fields: [] }, { name: 'unknown_command', fields: ['command'] }]
    const { api, fetchMock } = setup(json(200, { templates }))
    expect(await api.listTemplates()).toEqual(templates)
    expect(call(fetchMock)).toMatchObject({ url: '/api/admin/telegram/templates', method: 'GET' })
  })

  it('posts the template and data to preview', async () => {
    const { api, fetchMock } = setup(json(200, { html: 'I don’t know <code>/x</code>.', length: 26 }))
    expect(await api.previewTemplate('unknown_command', { command: 'x' })).toEqual({ html: 'I don’t know <code>/x</code>.', length: 26 })
    expect(call(fetchMock)).toEqual({
      url: '/api/admin/telegram/templates/preview',
      method: 'POST',
      body: { template: 'unknown_command', data: { command: 'x' } },
    })
  })

  it('does not trigger the app-wide forbidden screen on a playground 403', async () => {
    const { api, onAuthFailure } = setup(json(403, { detail: 'Forbidden' }))
    await expect(api.listTemplates()).rejects.toMatchObject({ status: 403 })
    expect(onAuthFailure).not.toHaveBeenCalled()
  })

  it('still ends the session on a playground 401', async () => {
    const { api, onAuthFailure } = setup(json(401, { detail: 'Unauthorized' }))
    await expect(api.listTemplates()).rejects.toBeInstanceOf(ApiError)
    expect(onAuthFailure).toHaveBeenCalledWith(401)
  })
})

describe('playground test-message client (FE-022)', () => {
  it('sends a test message with the template and data only, never a recipient', async () => {
    const { api, fetchMock } = setup(json(200, { messageId: 123 }))
    expect(await api.sendTestMessage('help', {})).toEqual({ messageId: 123 })
    expect(call(fetchMock)).toEqual({ url: '/api/admin/telegram/test-message', method: 'POST', body: { template: 'help', data: {} } })
  })

  it.each([
    [429, 'Test message limit reached (10 per hour)'],
    [409, 'TELEGRAM_BOT_TOKEN is not set'],
    [502, 'Telegram refused the message (SendFailed)'],
  ])('surfaces %i as ApiError with the detail', async (status, detail) => {
    await expect(setup(json(status, { detail })).api.sendTestMessage('help', {})).rejects.toMatchObject({ status, message: detail })
  })
})
