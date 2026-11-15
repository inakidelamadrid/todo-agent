import { create } from 'zustand'
import { type BillInput, type BillsApi, billsApi } from '../api/client'
import { monthOf, toDateKey } from '../model/schedule'
import { mergeMonthPayments, planImport } from '../model/sync'
import { addBill, markPaid, removeBill, undoPaid, updateBill } from '../model/transitions'
import type { Bill, BillsData, Line, MonthKey, Payment } from '../model/types'

export type LoadStatus = 'idle' | 'loading' | 'ready' | 'error'

export interface LoadError {
  /** 0 = API unreachable, 401 = bad key, otherwise the HTTP status. */
  readonly status: number
  readonly message: string
}

export interface BillsState extends BillsData {
  readonly billsStatus: LoadStatus
  readonly loadError: LoadError | null
  readonly months: Readonly<Record<MonthKey, LoadStatus>>
}

export interface BillsActions {
  readonly loadBills: () => Promise<void>
  readonly loadMonth: (month: MonthKey, options?: { readonly force?: boolean }) => Promise<void>
  /** Waits for the server (it assigns the id). Rejects with ApiError for the form to show. */
  readonly addBill: (input: BillInput) => Promise<Bill>
  /** Optimistic; rolls back and rejects on failure. */
  readonly updateBill: (bill: Bill) => Promise<Bill>
  readonly removeBill: (billId: string) => Promise<void>
  readonly markPaid: (payment: Payment) => Promise<void>
  readonly undoPaid: (billId: string, period: MonthKey) => Promise<void>
  /** Re-create a deleted bill and its payments (Undo for delete). */
  readonly restoreBill: (bill: Bill, payments: readonly Payment[]) => Promise<Bill>
  /** Import legacy browser data; resolves to how many items failed. */
  readonly importLegacy: (legacy: BillsData) => Promise<number>
}

const initial: BillsState = { bills: [], payments: [], billsStatus: 'idle', loadError: null, months: {} }

const errorOf = (e: unknown): LoadError => ({
  status: typeof e === 'object' && e !== null && 'status' in e ? Number((e as { status: unknown }).status) : 0,
  message: e instanceof Error ? e.message : 'Something went wrong',
})

const findPayment = (payments: readonly Payment[], billId: string, period: MonthKey) =>
  payments.find((p) => p.billId === billId && p.period === period)

const withoutId = ({ id: _id, ...rest }: Bill): BillInput => rest

/** Store factory with an injectable API, so actions are testable without a server. */
export const createBillsStore = (api: BillsApi) =>
  create<BillsState & BillsActions>()((set, get) => {
    const data = (): BillsData => ({ bills: get().bills, payments: get().payments })
    const apply = (next: BillsData) => set({ bills: next.bills, payments: next.payments })

    return {
      ...initial,

      loadBills: async () => {
        set({ billsStatus: 'loading', loadError: null })
        try {
          set({ bills: await api.listBills(), billsStatus: 'ready' })
        } catch (e) {
          set({ billsStatus: 'error', loadError: errorOf(e) })
        }
      },

      loadMonth: async (month, options) => {
        const status = get().months[month]
        if (!options?.force && (status === 'ready' || status === 'loading')) return
        set((s) => ({ months: { ...s.months, [month]: 'loading' } }))
        try {
          const fetched = await api.listPayments(month)
          set((s) => ({ payments: mergeMonthPayments(s.payments, month, fetched), months: { ...s.months, [month]: 'ready' } }))
        } catch (e) {
          set((s) => ({ months: { ...s.months, [month]: 'error' }, loadError: errorOf(e) }))
        }
      },

      addBill: async (input) => {
        const bill = await api.createBill(input)
        apply(addBill(data(), bill))
        return bill
      },

      updateBill: async (bill) => {
        const previous = get().bills.find((b) => b.id === bill.id)
        apply(updateBill(data(), bill))
        try {
          const saved = await api.updateBill(bill.id, withoutId(bill))
          apply(updateBill(data(), saved))
          return saved
        } catch (e) {
          if (previous) apply(updateBill(data(), previous))
          throw e
        }
      },

      removeBill: async (billId) => {
        const bill = get().bills.find((b) => b.id === billId)
        const removedPayments = get().payments.filter((p) => p.billId === billId)
        apply(removeBill(data(), billId))
        try {
          await api.deleteBill(billId)
        } catch (e) {
          if (bill) apply({ bills: [...get().bills, bill], payments: [...get().payments, ...removedPayments] })
          throw e
        }
      },

      markPaid: async (payment) => {
        const previous = findPayment(get().payments, payment.billId, payment.period)
        apply(markPaid(data(), payment))
        try {
          await api.putPayment(payment)
        } catch (e) {
          apply(previous ? markPaid(data(), previous) : undoPaid(data(), payment.billId, payment.period))
          throw e
        }
      },

      undoPaid: async (billId, period) => {
        const previous = findPayment(get().payments, billId, period)
        apply(undoPaid(data(), billId, period))
        try {
          await api.deletePayment(billId, period)
        } catch (e) {
          if (previous) apply(markPaid(data(), previous))
          throw e
        }
      },

      restoreBill: async (bill, payments) => {
        const created = await api.createBill(withoutId(bill))
        const moved = payments.map((p) => ({ ...p, billId: created.id }))
        await Promise.all(moved.map((p) => api.putPayment(p)))
        apply({ bills: [...get().bills, created], payments: [...get().payments, ...moved] })
        return created
      },

      importLegacy: async (legacy) => {
        const results = await Promise.allSettled(
          planImport(legacy).map(async (item) => {
            const created = await api.createBill(item.input)
            const paid = await Promise.allSettled(item.payments.map((p) => api.putPayment({ ...p, billId: created.id })))
            return paid.filter((r) => r.status === 'rejected').length
          }),
        )
        const failed = results.reduce((n, r) => n + (r.status === 'rejected' ? 1 : r.value), 0)
        set({ months: {}, payments: [] })
        await get().loadBills()
        return failed
      },
    }
  })

export const useBillsStore = createBillsStore(billsApi)

interface ViewState {
  readonly month: MonthKey
  readonly focusedLine: Line | null
  readonly setMonth: (month: MonthKey) => void
  readonly toggleLine: (line: Line) => void
}

/** Transient view state: which month is shown and which line is focused. */
export const useBillsViewStore = create<ViewState>()((set) => ({
  month: monthOf(toDateKey(new Date())),
  focusedLine: null,
  setMonth: (month) => set({ month }),
  toggleLine: (line) => set((s) => ({ focusedLine: s.focusedLine === line ? null : line })),
}))
