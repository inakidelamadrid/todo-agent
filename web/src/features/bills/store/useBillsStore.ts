import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { seedData } from '../data/seed'
import { monthOf, toDateKey } from '../model/schedule'
import { addBill, markPaid, type MarkPaidInput, removeBill, undoPaid, updateBill } from '../model/transitions'
import type { Bill, BillsData, Line, MonthKey } from '../model/types'

interface BillsActions {
  readonly markPaid: (input: MarkPaidInput) => void
  readonly undoPaid: (billId: string, period: MonthKey) => void
  readonly addBill: (bill: Bill) => void
  readonly updateBill: (bill: Bill) => void
  readonly removeBill: (billId: string) => void
}

/** Bills and payments, persisted to localStorage. Actions delegate to pure transitions. */
export const useBillsStore = create<BillsData & BillsActions>()(
  persist(
    (set) => ({
      ...seedData(toDateKey(new Date())),
      markPaid: (input) => set((s) => markPaid(s, input)),
      undoPaid: (billId, period) => set((s) => undoPaid(s, billId, period)),
      addBill: (bill) => set((s) => addBill(s, bill)),
      updateBill: (bill) => set((s) => updateBill(s, bill)),
      removeBill: (billId) => set((s) => removeBill(s, billId)),
    }),
    {
      name: 'todo-agent.bills',
      version: 1,
      partialize: ({ bills, payments }) => ({ bills, payments }),
    },
  ),
)

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
