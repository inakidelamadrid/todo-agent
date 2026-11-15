import type { BillInput } from '../api/client'
import type { Bill, BillsData, MonthKey, Payment } from './types'

/** Replace only `month`'s payments with what the server returned; other months stay. */
export const mergeMonthPayments = (
  payments: readonly Payment[],
  month: MonthKey,
  fetched: readonly Payment[],
): readonly Payment[] => [...payments.filter((p) => p.period !== month), ...fetched.filter((p) => p.period === month)]

/** Swap a bill's id everywhere (used when the server assigns a new id). */
export const replaceBillId = (data: BillsData, oldId: string, bill: Bill): BillsData => ({
  bills: data.bills.map((b) => (b.id === oldId ? bill : b)),
  payments: data.payments.map((p) => (p.billId === oldId ? { ...p, billId: bill.id } : p)),
})

export const LEGACY_STORAGE_KEY = 'todo-agent.bills'

/** Parse the pre-API localStorage payload (zustand persist). Returns null when absent or unusable. */
export const parseLegacy = (raw: string | null): BillsData | null => {
  if (!raw) return null
  try {
    const state = (JSON.parse(raw) as { state?: Partial<BillsData> }).state
    const bills = Array.isArray(state?.bills) ? state.bills : []
    const payments = Array.isArray(state?.payments) ? state.payments : []
    return bills.length > 0 ? { bills, payments } : null
  } catch {
    return null
  }
}

export interface ImportItem {
  readonly oldId: string
  readonly input: BillInput
  /** Payments to re-create once the server has assigned the new id. */
  readonly payments: readonly Omit<Payment, 'billId'>[]
}

/** Pure plan: one create per legacy bill, with its payments attached by old id. */
export const planImport = (legacy: BillsData): readonly ImportItem[] =>
  legacy.bills.map(({ id, ...input }) => ({
    oldId: id,
    input,
    payments: legacy.payments.filter((p) => p.billId === id).map(({ billId: _b, ...rest }) => rest),
  }))
