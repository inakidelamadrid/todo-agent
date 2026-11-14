export type Currency = 'MXN' | 'USD'
export type Recurrence = 'monthly' | 'bimonthly' | 'yearly'
export type Line = 'utilities' | 'telecom' | 'streaming' | 'software'
export type Status = 'overdue' | 'due-soon' | 'upcoming' | 'paid'

/** Month key, `YYYY-MM`. */
export type MonthKey = string
/** Calendar date, `YYYY-MM-DD`. */
export type DateKey = string

export interface Bill {
  readonly id: string
  readonly name: string
  readonly note: string
  readonly line: Line
  readonly currency: Currency
  /** Expected amount in cents. */
  readonly estimatedCents: number
  /** Day of month, 1–31; clamped to the month's last day. */
  readonly dueDay: number
  readonly recurrence: Recurrence
  /** First month the bill is due. */
  readonly startMonth: MonthKey
}

export interface Payment {
  readonly billId: string
  readonly period: MonthKey
  readonly actualCents: number
  readonly paidAt: DateKey
}

export interface BillsData {
  readonly bills: readonly Bill[]
  readonly payments: readonly Payment[]
}

export interface Occurrence {
  readonly bill: Bill
  readonly period: MonthKey
  readonly dueDate: DateKey
}

export interface CurrencyTotals {
  readonly totalCents: number
  readonly paidCents: number
  readonly remainingCents: number
}

export const CURRENCIES: readonly Currency[] = ['MXN', 'USD']
export const LINES: readonly Line[] = ['utilities', 'telecom', 'streaming', 'software']
export const STATUS_ORDER: readonly Status[] = ['overdue', 'due-soon', 'upcoming', 'paid']
