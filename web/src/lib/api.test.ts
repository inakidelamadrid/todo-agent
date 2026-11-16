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
