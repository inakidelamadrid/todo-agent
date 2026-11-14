import type {
  Bill,
  Currency,
  CurrencyTotals,
  DateKey,
  MonthKey,
  Occurrence,
  Payment,
  Recurrence,
  Status,
} from './types'
import { CURRENCIES, STATUS_ORDER } from './types'

const DUE_SOON_DAYS = 3
const STEP: Readonly<Record<Recurrence, number>> = { monthly: 1, bimonthly: 2, yearly: 12 }

const pad = (n: number): string => String(n).padStart(2, '0')

export const monthIndex = (month: MonthKey): number => {
  const [y, m] = month.split('-').map(Number)
  return y * 12 + (m - 1)
}

export const monthFromIndex = (index: number): MonthKey =>
  `${Math.floor(index / 12)}-${pad((index % 12) + 1)}`

export const addMonths = (month: MonthKey, n: number): MonthKey =>
  monthFromIndex(monthIndex(month) + n)

export const monthOf = (date: DateKey): MonthKey => date.slice(0, 7)

export const daysInMonth = (month: MonthKey): number => {
  const [y, m] = month.split('-').map(Number)
  return new Date(Date.UTC(y, m, 0)).getUTCDate()
}

export const toDateKey = (d: Date): DateKey =>
  `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

const dayNumber = (date: DateKey): number => {
  const [y, m, d] = date.split('-').map(Number)
  return Date.UTC(y, m - 1, d) / 86_400_000
}

export const daysBetween = (from: DateKey, to: DateKey): number => dayNumber(to) - dayNumber(from)

export const isDueInMonth = (bill: Bill, month: MonthKey): boolean => {
  const diff = monthIndex(month) - monthIndex(bill.startMonth)
  return diff >= 0 && diff % STEP[bill.recurrence] === 0
}

export const dueDateFor = (bill: Bill, month: MonthKey): DateKey =>
  `${month}-${pad(Math.min(bill.dueDay, daysInMonth(month)))}`

export const occurrencesForMonth = (bills: readonly Bill[], month: MonthKey): readonly Occurrence[] =>
  bills
    .filter((bill) => isDueInMonth(bill, month))
    .map((bill) => ({ bill, period: month, dueDate: dueDateFor(bill, month) }))
    .sort((a, b) => a.dueDate.localeCompare(b.dueDate) || a.bill.name.localeCompare(b.bill.name))

export const findPayment = (
  payments: readonly Payment[],
  billId: string,
  period: MonthKey,
): Payment | undefined => payments.find((p) => p.billId === billId && p.period === period)

export const statusOf = (occ: Occurrence, payments: readonly Payment[], today: DateKey): Status => {
  if (findPayment(payments, occ.bill.id, occ.period)) return 'paid'
  const days = daysBetween(today, occ.dueDate)
  if (days < 0) return 'overdue'
  return days <= DUE_SOON_DAYS ? 'due-soon' : 'upcoming'
}

/** Actual amount once paid, otherwise the estimate. */
export const amountOf = (occ: Occurrence, payments: readonly Payment[]): number =>
  findPayment(payments, occ.bill.id, occ.period)?.actualCents ?? occ.bill.estimatedCents

const emptyTotals: CurrencyTotals = { totalCents: 0, paidCents: 0, remainingCents: 0 }

export const totalsByCurrency = (
  occs: readonly Occurrence[],
  payments: readonly Payment[],
): Readonly<Record<Currency, CurrencyTotals>> => {
  const init = Object.fromEntries(CURRENCIES.map((c) => [c, emptyTotals])) as Record<Currency, CurrencyTotals>
  return occs.reduce<Record<Currency, CurrencyTotals>>((acc, occ) => {
    const cents = amountOf(occ, payments)
    const paid = findPayment(payments, occ.bill.id, occ.period) !== undefined
    const prev = acc[occ.bill.currency]
    return {
      ...acc,
      [occ.bill.currency]: {
        totalCents: prev.totalCents + cents,
        paidCents: prev.paidCents + (paid ? cents : 0),
        remainingCents: prev.remainingCents + (paid ? 0 : cents),
      },
    }
  }, init)
}

export interface StatusGroup {
  readonly status: Status
  readonly items: readonly Occurrence[]
}

export const groupByStatus = (
  occs: readonly Occurrence[],
  payments: readonly Payment[],
  today: DateKey,
): readonly StatusGroup[] =>
  STATUS_ORDER.map((status) => ({
    status,
    items: occs.filter((o) => statusOf(o, payments, today) === status),
  })).filter((g) => g.items.length > 0)

const LOCALE: Readonly<Record<Currency, string>> = { MXN: 'es-MX', USD: 'en-US' }

export const formatMoney = (cents: number, currency: Currency): string =>
  new Intl.NumberFormat(LOCALE[currency], {
    style: 'currency',
    currency,
    currencyDisplay: 'narrowSymbol',
    minimumFractionDigits: 2,
  }).format(cents / 100)

export const toCents = (value: string): number | null => {
  const n = Number(value.replace(/[,\s$]/g, ''))
  return Number.isFinite(n) && n >= 0 ? Math.round(n * 100) : null
}

export const formatMonth = (month: MonthKey): string => {
  const [y, m] = month.split('-').map(Number)
  return new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(
    new Date(Date.UTC(y, m - 1, 1)),
  )
}

export const formatDay = (date: DateKey): string => {
  const [y, m, d] = date.split('-').map(Number)
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' }).format(
    new Date(Date.UTC(y, m - 1, d)),
  )
}

export const relativeDue = (occ: Occurrence, today: DateKey): string => {
  const days = daysBetween(today, occ.dueDate)
  if (days === 0) return 'Due today'
  if (days === 1) return 'Tomorrow'
  if (days === -1) return '1 day late'
  return days < 0 ? `${-days} days late` : `In ${days} days`
}
