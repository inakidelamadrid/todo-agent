import { describe, expect, it, vi } from 'vitest'
import type { Bill } from '../model/types'
import { createBillsApi } from './client'

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
})
