import { describe, expect, it, vi } from 'vitest'
import type { BillsApi } from '../api/client'
import { ApiError } from '../api/client'
import { mergeMonthPayments, parseLegacy, planImport } from '../model/sync'
import type { Bill, Payment } from '../model/types'
import { createBillsStore } from './useBillsStore'

const bill = (over: Partial<Bill> = {}): Bill => ({
  id: 'b1',
  name: 'Izzi',
  note: '',
  line: 'telecom',
  currency: 'MXN',
  estimatedCents: 64_900,
  dueDay: 15,
  recurrence: 'monthly',
  startMonth: '2026-01',
  ...over,
})

const pay = (over: Partial<Payment> = {}): Payment => ({
  billId: 'b1',
  period: '2026-11',
  actualCents: 64_900,
  paidAt: '2026-11-14',
  ...over,
})

const fakeApi = (over: Partial<BillsApi> = {}): BillsApi => ({
  listBills: vi.fn(async () => [bill()]),
  createBill: vi.fn(async (input) => ({ ...input, id: 'new-1' })),
  updateBill: vi.fn(async (id, patch) => ({ ...bill(), ...patch, id })),
  deleteBill: vi.fn(async () => undefined),
  listPayments: vi.fn(async () => []),
  putPayment: vi.fn(async (p) => p),
  deletePayment: vi.fn(async () => undefined),
  ...over,
})

const offline = () => Promise.reject(new ApiError(0, 'Can’t reach the bills API'))

const loaded = async (api: BillsApi) => {
  const store = createBillsStore(api)
  await store.getState().loadBills()
  return store
}

describe('bills store', () => {
  it('loads bills and records errors with their status', async () => {
    const ok = await loaded(fakeApi())
    expect(ok.getState()).toMatchObject({ billsStatus: 'ready', bills: [bill()] })

    const bad = await loaded(fakeApi({ listBills: () => Promise.reject(new ApiError(401, 'nope')) }))
    expect(bad.getState()).toMatchObject({ billsStatus: 'error', loadError: { status: 401 } })
  })

  it('loads each month once unless forced', async () => {
    const api = fakeApi({ listPayments: vi.fn(async (month: string) => [pay({ period: month })]) })
    const store = await loaded(api)
    await store.getState().loadMonth('2026-11')
    await store.getState().loadMonth('2026-11')
    expect(api.listPayments).toHaveBeenCalledTimes(1)
    await store.getState().loadMonth('2026-11', { force: true })
    expect(api.listPayments).toHaveBeenCalledTimes(2)
    expect(store.getState().months['2026-11']).toBe('ready')
  })

  it('marks paid optimistically', async () => {
    let resolve!: () => void
    const api = fakeApi({ putPayment: vi.fn(() => new Promise<Payment>((r) => (resolve = () => r(pay())))) })
    const store = await loaded(api)
    const pending = store.getState().markPaid(pay())
    expect(store.getState().payments).toEqual([pay()])
    resolve()
    await pending
    expect(store.getState().payments).toEqual([pay()])
  })

  it('rolls back a failed mark paid, restoring an earlier amount', async () => {
    const store = await loaded(fakeApi({ putPayment: offline }))
    store.setState({ payments: [pay({ actualCents: 100 })] })
    await expect(store.getState().markPaid(pay({ actualCents: 999 }))).rejects.toBeInstanceOf(ApiError)
    expect(store.getState().payments).toEqual([pay({ actualCents: 100 })])

    store.setState({ payments: [] })
    await expect(store.getState().markPaid(pay())).rejects.toBeInstanceOf(ApiError)
    expect(store.getState().payments).toEqual([])
  })

  it('rolls back a failed undo', async () => {
    const store = await loaded(fakeApi({ deletePayment: offline }))
    store.setState({ payments: [pay()] })
    await expect(store.getState().undoPaid('b1', '2026-11')).rejects.toBeInstanceOf(ApiError)
    expect(store.getState().payments).toEqual([pay()])
  })

  it('rolls back a failed delete, bill and payments', async () => {
    const store = await loaded(fakeApi({ deleteBill: offline }))
    store.setState({ payments: [pay()] })
    await expect(store.getState().removeBill('b1')).rejects.toBeInstanceOf(ApiError)
    expect(store.getState().bills).toEqual([bill()])
    expect(store.getState().payments).toEqual([pay()])
  })

  it('rolls back a failed edit', async () => {
    const store = await loaded(fakeApi({ updateBill: () => Promise.reject(new ApiError(422, 'bad', { name: 'x' })) }))
    await expect(store.getState().updateBill(bill({ name: 'Renamed' }))).rejects.toMatchObject({ status: 422 })
    expect(store.getState().bills).toEqual([bill()])
  })

  it('adds a bill with the server id', async () => {
    const store = await loaded(fakeApi())
    const { id: _id, ...input } = bill({ name: 'Disney+' })
    const created = await store.getState().addBill(input)
    expect(created.id).toBe('new-1')
    expect(store.getState().bills.map((b) => b.id)).toEqual(['b1', 'new-1'])
  })

  it('restores a deleted bill under a new id with its payments', async () => {
    const api = fakeApi()
    const store = await loaded(api)
    store.setState({ bills: [] })
    const restored = await store.getState().restoreBill(bill(), [pay()])
    expect(restored.id).toBe('new-1')
    expect(api.putPayment).toHaveBeenCalledWith(pay({ billId: 'new-1' }))
    expect(store.getState().payments).toEqual([pay({ billId: 'new-1' })])
  })
})

describe('sync helpers', () => {
  it('replaces only the requested month', () => {
    const before = [pay({ period: '2026-10' }), pay({ period: '2026-11', actualCents: 1 })]
    const after = mergeMonthPayments(before, '2026-11', [pay({ period: '2026-11', actualCents: 2 }), pay({ period: '2026-12' })])
    expect(after).toEqual([pay({ period: '2026-10' }), pay({ period: '2026-11', actualCents: 2 })])
  })

  it('parses legacy storage and ignores empty or broken payloads', () => {
    const raw = JSON.stringify({ state: { bills: [bill()], payments: [pay()] }, version: 1 })
    expect(parseLegacy(raw)).toEqual({ bills: [bill()], payments: [pay()] })
    expect(parseLegacy(JSON.stringify({ state: { bills: [], payments: [] } }))).toBeNull()
    expect(parseLegacy('{not json')).toBeNull()
    expect(parseLegacy(null)).toBeNull()
  })

  it('plans an import that carries payments to the new id', async () => {
    const legacy = { bills: [bill(), bill({ id: 'b2', name: 'Telcel' })], payments: [pay(), pay({ billId: 'b2' })] }
    expect(planImport(legacy)[0]).toMatchObject({ oldId: 'b1', input: { name: 'Izzi' }, payments: [{ period: '2026-11' }] })

    let n = 0
    const api = fakeApi({ createBill: vi.fn(async (input) => ({ ...input, id: `srv-${++n}` })), listBills: vi.fn(async () => []) })
    const store = createBillsStore(api)
    expect(await store.getState().importLegacy(legacy)).toBe(0)
    expect(api.putPayment).toHaveBeenCalledWith(expect.objectContaining({ billId: 'srv-1' }))
    expect(api.putPayment).toHaveBeenCalledWith(expect.objectContaining({ billId: 'srv-2' }))
  })

  it('counts failed imports instead of throwing', async () => {
    const api = fakeApi({ createBill: offline, listBills: vi.fn(async () => []) })
    const store = createBillsStore(api)
    expect(await store.getState().importLegacy({ bills: [bill()], payments: [] })).toBe(1)
  })
})
