import { Plus } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { findPayment, formatDay, formatMoney, formatMonth, groupByStatus, monthOf, occurrencesForMonth, statusOf, toDateKey, totalsByCurrency } from '../model/schedule'
import type { Bill, DateKey, Occurrence } from '../model/types'
import { useBillsStore, useBillsViewStore } from '../store/useBillsStore'
import { BillFormSheet } from './BillFormSheet'
import { BillTable } from './BillTable'
import { EmptyState } from './EmptyState'
import { MonthSwitcher } from './MonthSwitcher'
import { NetworkMap } from './NetworkMap'
import { SummaryStrip } from './SummaryStrip'

const headline = (occs: readonly Occurrence[], paidCount: number, next: Occurrence | undefined): string =>
  [
    `${occs.length} ${occs.length === 1 ? 'bill' : 'bills'}`,
    `${paidCount} paid`,
    next ? `next: ${next.bill.name}, ${formatDay(next.dueDate)}` : occs.length ? 'all paid' : null,
  ]
    .filter(Boolean)
    .join(' · ')

export const BillsMonthView = () => {
  const bills = useBillsStore((s) => s.bills)
  const payments = useBillsStore((s) => s.payments)
  const { markPaid, undoPaid, addBill, updateBill, removeBill } = useBillsStore.getState()
  const { month, focusedLine, setMonth, toggleLine } = useBillsViewStore()

  const [sheet, setSheet] = useState<{ open: boolean; bill: Bill | null }>({ open: false, bill: null })
  const [highlightedId, setHighlightedId] = useState<string | null>(null)

  const today: DateKey = toDateKey(new Date())
  const occurrences = occurrencesForMonth(bills, month)
  const visible = focusedLine ? occurrences.filter((o) => o.bill.line === focusedLine) : occurrences
  const groups = groupByStatus(visible, payments, today)
  const paidCount = occurrences.filter((o) => findPayment(payments, o.bill.id, o.period)).length
  const next = occurrences.find((o) => statusOf(o, payments, today) !== 'paid')

  const pay = (occ: Occurrence, actualCents: number, paidAt: DateKey) => {
    markPaid({ billId: occ.bill.id, period: occ.period, actualCents, paidAt })
    toast.success(`${occ.bill.name} paid · ${formatMoney(actualCents, occ.bill.currency)}`, {
      action: { label: 'Undo', onClick: () => undoPaid(occ.bill.id, occ.period) },
    })
  }

  const undo = (occ: Occurrence) => {
    const payment = findPayment(payments, occ.bill.id, occ.period)
    undoPaid(occ.bill.id, occ.period)
    if (payment) toast(`${occ.bill.name} marked unpaid`, { action: { label: 'Redo', onClick: () => markPaid(payment) } })
  }

  const selectBill = (billId: string) => {
    const row = document.getElementById(`bill-${billId}`) ?? document.getElementById(`bill-m-${billId}`)
    row?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    row?.focus({ preventScroll: true })
    setHighlightedId(billId)
    window.setTimeout(() => setHighlightedId((id) => (id === billId ? null : id)), 1600)
  }

  const save = (bill: Bill) => {
    const exists = bills.some((b) => b.id === bill.id)
    if (exists) updateBill(bill)
    else addBill(bill)
    setSheet({ open: false, bill: null })
    toast.success(exists ? `${bill.name} updated` : `${bill.name} added`)
  }

  const remove = (bill: Bill) => {
    const removedPayments = payments.filter((p) => p.billId === bill.id)
    removeBill(bill.id)
    setSheet({ open: false, bill: null })
    toast(`${bill.name} deleted`, {
      action: {
        label: 'Undo',
        onClick: () => {
          addBill(bill)
          removedPayments.forEach(markPaid)
        },
      },
    })
  }

  return (
    <div className="mx-auto flex max-w-[90rem] flex-col gap-5 [&>*]:min-w-0 px-4 py-6 md:px-8 md:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-heading text-4xl font-semibold tracking-tight md:text-5xl">{formatMonth(month)}</h1>
          <p className="mt-1 text-muted-foreground">{headline(occurrences, paidCount, next)}</p>
          <p className="mt-1 text-sm text-muted-foreground md:hidden">Sample bills included · saved in this browser</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <MonthSwitcher month={month} currentMonth={monthOf(today)} onChange={setMonth} />
          <Button onClick={() => setSheet({ open: true, bill: null })}>
            <Plus aria-hidden="true" />
            Add bill
          </Button>
        </div>
      </header>

      {bills.length === 0 ? (
        <EmptyState onAdd={() => setSheet({ open: true, bill: null })} />
      ) : (
        <>
          <SummaryStrip totals={totalsByCurrency(occurrences, payments)} />
          <NetworkMap
            month={month}
            today={today}
            occurrences={occurrences}
            payments={payments}
            focusedLine={focusedLine}
            onToggleLine={toggleLine}
            onSelectBill={selectBill}
          />
          <BillTable
            month={month}
            today={today}
            groups={groups}
            payments={payments}
            highlightedId={highlightedId}
            onPay={pay}
            onUndo={undo}
            onEdit={(bill) => setSheet({ open: true, bill })}
          />
        </>
      )}

      <BillFormSheet
        open={sheet.open}
        bill={sheet.bill}
        defaultMonth={month}
        onOpenChange={(open) => setSheet((s) => ({ ...s, open }))}
        onSave={save}
        onDelete={remove}
      />
    </div>
  )
}
