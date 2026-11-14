import type { Bill, BillsData, DateKey, MonthKey, Payment } from './types'

export interface MarkPaidInput {
  readonly billId: string
  readonly period: MonthKey
  readonly actualCents: number
  readonly paidAt: DateKey
}

const samePayment = (billId: string, period: MonthKey) => (p: Payment) =>
  p.billId === billId && p.period === period

export const markPaid = (data: BillsData, input: MarkPaidInput): BillsData => ({
  ...data,
  payments: [...data.payments.filter((p) => !samePayment(input.billId, input.period)(p)), input],
})

export const undoPaid = (data: BillsData, billId: string, period: MonthKey): BillsData => ({
  ...data,
  payments: data.payments.filter((p) => !samePayment(billId, period)(p)),
})

export const addBill = (data: BillsData, bill: Bill): BillsData => ({
  ...data,
  bills: [...data.bills, bill],
})

export const updateBill = (data: BillsData, bill: Bill): BillsData => ({
  ...data,
  bills: data.bills.map((b) => (b.id === bill.id ? bill : b)),
})

export const removeBill = (data: BillsData, billId: string): BillsData => ({
  bills: data.bills.filter((b) => b.id !== billId),
  payments: data.payments.filter((p) => p.billId !== billId),
})
