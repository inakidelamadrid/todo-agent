import { describe, expect, it, vi } from 'vitest'
import type { Bill } from '../model/types'
import { ApiError, createBillsApi, toFieldErrors } from './client'

const bill: Bill = {
  id: 'b1',
  name: 'CFE',
  note: '',
  line: 'utilities',
  currency: 'MXN',
  estimatedCents: 124_000,
  dueDay: 8,
  recurrence: 'bimonthly',
  startMonth: '2026-01',
}

const json = (status: number, body: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

const setup = (response: Response | Error) => {
  const fetchMock = vi.fn(async () => {
    if (response instanceof Error) throw response
    return response
  })
  return { api: createBillsApi(fetchMock as unknown as typeof fetch), fetchMock }
}

const call = (fetchMock: ReturnType<typeof vi.fn>) => {
  const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
  return { url, method: init.method, body: init.body ? JSON.parse(init.body as string) : undefined }
}

describe('bills API client', () => {
  it('lists bills and strips server-only fields', async () => {
    const { api, fetchMock } = setup(json(200, [{ ...bill, createdAt: 'x', updatedAt: 'y' }]))
    expect(await api.listBills()).toEqual([bill])
    expect(call(fetchMock)).toMatchObject({ url: '/api/bills', method: 'GET' })
  })

  it('creates a bill with a camelCase body and no id', async () => {
    const { api, fetchMock } = setup(json(201, bill))
    const { id: _id, ...input } = bill
    await api.createBill(input)
    expect(call(fetchMock)).toEqual({ url: '/api/bills', method: 'POST', body: input })
  })

  it('patches, deletes and lists payments for a month', async () => {
    const patch = setup(json(200, bill))
    await patch.api.updateBill('b1', { name: 'CFE' })
    expect(call(patch.fetchMock)).toEqual({ url: '/api/bills/b1', method: 'PATCH', body: { name: 'CFE' } })

    const del = setup(json(204, undefined))
    await expect(del.api.deleteBill('b1')).resolves.toBeUndefined()
    expect(call(del.fetchMock)).toMatchObject({ url: '/api/bills/b1', method: 'DELETE' })

    const list = setup(json(200, []))
    await list.api.listPayments('2026-11')
    expect(call(list.fetchMock)).toMatchObject({ url: '/api/payments?month=2026-11', method: 'GET' })
  })

  it('upserts and deletes a payment by bill and period', async () => {
    const payment = { billId: 'b1', period: '2026-11', actualCents: 71_240, paidAt: '2026-11-14' }
    const put = setup(json(200, payment))
    await put.api.putPayment(payment)
    expect(call(put.fetchMock)).toEqual({
      url: '/api/bills/b1/payments/2026-11',
      method: 'PUT',
      body: { actualCents: 71_240, paidAt: '2026-11-14' },
    })

    const del = setup(json(204, undefined))
    await del.api.deletePayment('b1', '2026-11')
    expect(call(del.fetchMock)).toMatchObject({ url: '/api/bills/b1/payments/2026-11', method: 'DELETE' })
  })

  it.each([
    [401, { detail: 'Invalid or missing API key' }, 'Invalid or missing API key'],
    [404, { detail: 'Bill not found' }, 'Bill not found'],
    [500, null, 'Request failed (500)'],
  ])('maps %s to ApiError', async (status, body, message) => {
    const { api } = setup(json(status, body))
    const error = await api.listBills().catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status, message })
  })

  it('maps 422 validation details to camelCase field errors', async () => {
    const detail = [
      { loc: ['body', 'estimatedCents'], msg: 'Input should be greater than or equal to 0' },
      { loc: ['body', 'dueDay'], msg: 'Input should be less than or equal to 31' },
    ]
    const { api } = setup(json(422, { detail }))
    const error = (await api.createBill({ ...bill }).catch((e: unknown) => e)) as ApiError
    expect(error.status).toBe(422)
    expect(error.fieldErrors).toEqual({
      estimatedCents: 'Input should be greater than or equal to 0',
      dueDay: 'Input should be less than or equal to 31',
    })
  })

  it('reports a network failure as status 0', async () => {
    const { api } = setup(new TypeError('Failed to fetch'))
    await expect(api.listBills()).rejects.toMatchObject({ status: 0, message: 'Can’t reach the bills API' })
  })

  it('ignores non-array 422 details', () => {
    expect(toFieldErrors('Bill is not due')).toEqual({})
  })
})
