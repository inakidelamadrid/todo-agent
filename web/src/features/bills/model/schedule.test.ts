import { describe, expect, it } from 'vitest'
import {
  addMonths,
  amountOf,
  formatMoney,
  groupByStatus,
  occurrencesForMonth,
  statusOf,
  toCents,
  totalsByCurrency,
} from './schedule'
import { addBill, markPaid, removeBill, undoPaid, updateBill } from './transitions'
import type { Bill, BillsData } from './types'

const bill = (over: Partial<Bill>): Bill => ({
  id: 'b',
  name: 'Bill',
  note: '',
  line: 'utilities',
  currency: 'MXN',
  estimatedCents: 10_000,
  dueDay: 10,
  recurrence: 'monthly',
  startMonth: '2026-01',
  ...over,
})

describe('occurrencesForMonth', () => {
  it('includes monthly bills from their start month on', () => {
    const b = bill({ startMonth: '2026-03' })
    expect(occurrencesForMonth([b], '2026-02')).toHaveLength(0)
    expect(occurrencesForMonth([b], '2026-03')).toHaveLength(1)
  })

  it('includes bimonthly bills every other month', () => {
    const b = bill({ recurrence: 'bimonthly', startMonth: '2026-01' })
    expect(occurrencesForMonth([b], '2026-11')).toHaveLength(1)
    expect(occurrencesForMonth([b], '2026-12')).toHaveLength(0)
  })

  it('includes yearly bills once a year, across year boundaries', () => {
    const b = bill({ recurrence: 'yearly', startMonth: '2025-11' })
    expect(occurrencesForMonth([b], '2026-11')).toHaveLength(1)
    expect(occurrencesForMonth([b], '2027-10')).toHaveLength(0)
  })

  it('clamps the due day to the end of short months and sorts by date', () => {
    const occ = occurrencesForMonth([bill({ id: 'x', dueDay: 31 }), bill({ id: 'y', dueDay: 2 })], '2026-02')
    expect(occ.map((o) => o.dueDate)).toEqual(['2026-02-02', '2026-02-28'])
  })
})

describe('statusOf', () => {
  const [occ] = occurrencesForMonth([bill({ dueDay: 15 })], '2026-11')
  it.each([
    ['2026-11-16', 'overdue'],
    ['2026-11-15', 'due-soon'],
    ['2026-11-12', 'due-soon'],
    ['2026-11-11', 'upcoming'],
  ])('on %s is %s', (today, expected) => {
    expect(statusOf(occ, [], today)).toBe(expected)
  })
  it('is paid once a payment exists, even when late', () => {
    const payments = [{ billId: 'b', period: '2026-11', actualCents: 1, paidAt: '2026-11-20' }]
    expect(statusOf(occ, payments, '2026-11-30')).toBe('paid')
  })
})

describe('totals', () => {
  const bills = [
    bill({ id: 'a', estimatedCents: 50_000 }),
    bill({ id: 'b', estimatedCents: 20_000 }),
    bill({ id: 'c', currency: 'USD', estimatedCents: 999 }),
  ]
  const occs = occurrencesForMonth(bills, '2026-11')
  const payments = [{ billId: 'a', period: '2026-11', actualCents: 61_250, paidAt: '2026-11-10' }]

  it('uses the actual amount once paid and the estimate otherwise', () => {
    expect(amountOf(occs[0], payments)).toBe(61_250)
    expect(amountOf(occs[1], payments)).toBe(20_000)
  })

  it('keeps each currency separate', () => {
    const t = totalsByCurrency(occs, payments)
    expect(t.MXN).toEqual({ totalCents: 81_250, paidCents: 61_250, remainingCents: 20_000 })
    expect(t.USD).toEqual({ totalCents: 999, paidCents: 0, remainingCents: 999 })
  })

  it('groups in overdue, due soon, upcoming, paid order', () => {
    const groups = groupByStatus(occs, payments, '2026-11-09')
    expect(groups.map((g) => g.status)).toEqual(['due-soon', 'paid'])
  })
})

describe('transitions', () => {
  const data: BillsData = { bills: [bill({ id: 'a' })], payments: [] }
  const paid = markPaid(data, { billId: 'a', period: '2026-11', actualCents: 123, paidAt: '2026-11-01' })

  it('marks paid without mutating, replacing any earlier payment', () => {
    expect(data.payments).toHaveLength(0)
    const again = markPaid(paid, { billId: 'a', period: '2026-11', actualCents: 456, paidAt: '2026-11-02' })
    expect(again.payments).toEqual([{ billId: 'a', period: '2026-11', actualCents: 456, paidAt: '2026-11-02' }])
  })

  it('undoes a payment', () => {
    expect(undoPaid(paid, 'a', '2026-11').payments).toHaveLength(0)
  })

  it('adds, updates and removes bills; removal drops their payments', () => {
    const added = addBill(paid, bill({ id: 'z' }))
    expect(added.bills.map((b) => b.id)).toEqual(['a', 'z'])
    expect(updateBill(added, bill({ id: 'z', name: 'New' })).bills[1].name).toBe('New')
    expect(removeBill(added, 'a')).toEqual({ bills: [bill({ id: 'z' })], payments: [] })
  })
})

describe('helpers', () => {
  it('adds months across years', () => {
    expect(addMonths('2026-12', 1)).toBe('2027-01')
    expect(addMonths('2026-01', -1)).toBe('2025-12')
  })
  it('parses and formats money', () => {
    expect(toCents('1,240.50')).toBe(124_050)
    expect(toCents('abc')).toBeNull()
    expect(toCents('-5')).toBeNull()
    expect(formatMoney(124_050, 'MXN')).toBe('$1,240.50')
    expect(formatMoney(999, 'USD')).toBe('$9.99')
  })
})
