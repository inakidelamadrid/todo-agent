import { describe, expect, it, vi } from 'vitest'
import { ApiError, createRequest, toFieldErrors } from './api'

const json = (status: number, body: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

const setup = (response: Response | Error) => {
  const fetchMock = vi.fn(async () => {
    if (response instanceof Error) throw response
    return response
  })
  return { request: createRequest(fetchMock as unknown as typeof fetch, '/api'), fetchMock }
}

describe('request', () => {
  it.each([
    [401, { detail: 'Invalid or missing API key' }, 'Invalid or missing API key'],
    [404, { detail: 'Bill not found' }, 'Bill not found'],
    [500, null, 'Request failed (500)'],
  ])('maps %s to ApiError', async (status, body, message) => {
    const { request } = setup(json(status, body))
    const error = await request('GET', '/bills').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status, message })
  })

  it('turns a 422 into ApiError with field errors', async () => {
    const detail = [
      { loc: ['body', 'estimatedCents'], msg: 'Input should be greater than or equal to 0' },
      { loc: ['body', 'dueDay'], msg: 'Input should be less than or equal to 31' },
    ]
    const { request } = setup(json(422, { detail }))
    const error = (await request('POST', '/bills', {}).catch((e: unknown) => e)) as ApiError
    expect(error.status).toBe(422)
    expect(error.fieldErrors).toEqual({
      estimatedCents: 'Input should be greater than or equal to 0',
      dueDay: 'Input should be less than or equal to 31',
    })
  })

  it('turns a network failure into ApiError', async () => {
    const { request } = setup(new TypeError('Failed to fetch'))
    await expect(request('GET', '/bills')).rejects.toMatchObject({ status: 0, message: 'Can’t reach the bills API' })
  })

  it('ignores non-array 422 details', () => {
    expect(toFieldErrors('Bill is not due')).toEqual({})
  })
})

describe('request with a token getter', () => {
  const TOKEN = 'session-token-abc'

  const setupAuth = (getToken: (() => Promise<string | null>) | undefined, status = 200) => {
    const fetchMock = vi.fn(async () => json(status, status === 200 ? [] : { detail: 'Invalid or missing credentials' }))
    return { request: createRequest(fetchMock as unknown as typeof fetch, '/api', getToken), fetchMock }
  }

  const headersOf = (fetchMock: ReturnType<typeof vi.fn>, index = 0) =>
    (fetchMock.mock.calls[index] as [string, RequestInit])[1].headers as Record<string, string>

  it('adds a bearer header when a token is returned', async () => {
    const { request, fetchMock } = setupAuth(async () => TOKEN)
    await request('GET', '/bills')
    expect(headersOf(fetchMock)).toEqual({ Accept: 'application/json', Authorization: `Bearer ${TOKEN}` })
  })

  it('sends no header when the token is null', async () => {
    const { request, fetchMock } = setupAuth(async () => null)
    await request('GET', '/bills')
    expect(headersOf(fetchMock)).not.toHaveProperty('Authorization')
  })

  it('sends no header, and still sends the request, when the getter rejects', async () => {
    const { request, fetchMock } = setupAuth(async () => {
      throw new Error('clerk is down')
    })
    await expect(request('GET', '/bills')).resolves.toEqual([])
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(headersOf(fetchMock)).not.toHaveProperty('Authorization')
  })

  it('asks for a fresh token on every request', async () => {
    const getToken = vi.fn().mockResolvedValueOnce('first').mockResolvedValueOnce('second')
    const { request, fetchMock } = setupAuth(getToken)
    await request('GET', '/bills')
    await request('GET', '/bills')
    expect(getToken).toHaveBeenCalledTimes(2)
    expect(headersOf(fetchMock, 0).Authorization).toBe('Bearer first')
    expect(headersOf(fetchMock, 1).Authorization).toBe('Bearer second')
  })

  it('never puts the token in a thrown ApiError', async () => {
    const { request } = setupAuth(async () => TOKEN, 401)
    const error = (await request('GET', '/bills').catch((e: unknown) => e)) as ApiError
    expect(error.status).toBe(401)
    expect(JSON.stringify({ ...error, message: error.message, stack: error.stack })).not.toContain(TOKEN)
  })

  it('leaves existing calls unchanged without a getter', async () => {
    const { request, fetchMock } = setupAuth(undefined)
    await request('POST', '/bills', { name: 'CFE' })
    expect(headersOf(fetchMock)).toEqual({ Accept: 'application/json', 'Content-Type': 'application/json' })
  })
})
