import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { isApiError } from '../api/client'
import { findPayment, formatDay, formatMoney, formatMonth, groupByStatus, monthOf, occurrencesForMonth, statusOf, toDateKey, totalsByCurrency } from '../model/schedule'
import { LEGACY_STORAGE_KEY, parseLegacy } from '../model/sync'
import type { Bill, BillsData, DateKey, Occurrence } from '../model/types'
import { useBillsStore, useBillsViewStore } from '../store/useBillsStore'
import { BillFormSheet } from './BillFormSheet'
import { BillTable } from './BillTable'
import { EmptyState } from './EmptyState'
import { BillsSkeleton, ImportBanner, LoadErrorPanel } from './LoadStates'
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

const readLegacy = (): BillsData | null => {
  try {
    return parseLegacy(window.localStorage.getItem(LEGACY_STORAGE_KEY))
  } catch {
    return null
  }
}

const clearLegacy = () => {
  try {
    window.localStorage.removeItem(LEGACY_STORAGE_KEY)
  } catch {
    /* storage unavailable: nothing to clear */
  }
}

const failed = (what: string) => (e: unknown) =>
  toast.error(`${what} didn’t save`, { description: isApiError(e) ? e.message : 'Something went wrong. Try again.' })

export const BillsMonthView = () => {
  const bills = useBillsStore((s) => s.bills)
  const payments = useBillsStore((s) => s.payments)
  const billsStatus = useBillsStore((s) => s.billsStatus)
  const loadError = useBillsStore((s) => s.loadError)
  const { month, focusedLine, setMonth, toggleLine } = useBillsViewStore()
  const monthStatus = useBillsStore((s) => s.months[month] ?? 'idle')
  const actions = useBillsStore.getState()

  const [sheet, setSheet] = useState<{ open: boolean; bill: Bill | null }>({ open: false, bill: null })
  const [highlightedId, setHighlightedId] = useState<string | null>(null)
  const [legacy, setLegacy] = useState<BillsData | null>(readLegacy)

  const today: DateKey = toDateKey(new Date())

  useEffect(() => {
    void useBillsStore.getState().loadBills()
    void useBillsStore.getState().loadMonth(monthOf(toDateKey(new Date())))
  }, [])

  useEffect(() => {
    void useBillsStore.getState().loadMonth(month)
  }, [month])

  const occurrences = occurrencesForMonth(bills, month)
  const visible = focusedLine ? occurrences.filter((o) => o.bill.line === focusedLine) : occurrences
  const groups = groupByStatus(visible, payments, today)
  const paidCount = occurrences.filter((o) => findPayment(payments, o.bill.id, o.period)).length
  const next = occurrences.find((o) => statusOf(o, payments, today) !== 'paid')

  const loading = billsStatus === 'idle' || billsStatus === 'loading' || monthStatus === 'idle' || monthStatus === 'loading'
  const errored = billsStatus === 'error' || monthStatus === 'error'
  const ready = !loading && !errored
  const showImport = billsStatus === 'ready' && bills.length === 0 && legacy !== null

  const retry = () => {
    void actions.loadBills()
    void actions.loadMonth(month, { force: true })
  }

  const pay = (occ: Occurrence, actualCents: number, paidAt: DateKey) => {
    const payment = { billId: occ.bill.id, period: occ.period, actualCents, paidAt }
    actions.markPaid(payment).then(
      () =>
        toast.success(`${occ.bill.name} paid · ${formatMoney(actualCents, occ.bill.currency)}`, {
          action: { label: 'Undo', onClick: () => actions.undoPaid(occ.bill.id, occ.period).catch(failed('Undo')) },
        }),
      failed(`${occ.bill.name} payment`),
    )
  }

  const undo = (occ: Occurrence) => {
    const payment = findPayment(payments, occ.bill.id, occ.period)
    actions.undoPaid(occ.bill.id, occ.period).then(
      () =>
        payment &&
        toast(`${occ.bill.name} marked unpaid`, {
          action: { label: 'Redo', onClick: () => actions.markPaid(payment).catch(failed('Redo')) },
        }),
      failed('Undo'),
    )
  }

  const selectBill = (billId: string) => {
    const row = document.getElementById(`bill-${billId}`) ?? document.getElementById(`bill-m-${billId}`)
    row?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    row?.focus({ preventScroll: true })
    setHighlightedId(billId)
    window.setTimeout(() => setHighlightedId((id) => (id === billId ? null : id)), 1600)
  }

  /** Rejects with ApiError so the sheet can show the server's field errors. */
  const save = async (bill: Bill, isNew: boolean) => {
    const saved = isNew ? await actions.addBill((({ id: _id, ...rest }) => rest)(bill)) : await actions.updateBill(bill)
    setSheet({ open: false, bill: null })
    toast.success(isNew ? `${saved.name} added` : `${saved.name} updated`)
  }

  const remove = (bill: Bill) => {
    const removedPayments = payments.filter((p) => p.billId === bill.id)
    setSheet({ open: false, bill: null })
    actions.removeBill(bill.id).then(
      () =>
        toast(`${bill.name} deleted`, {
          action: { label: 'Undo', onClick: () => actions.restoreBill(bill, removedPayments).catch(failed('Undo')) },
        }),
      failed(`Deleting ${bill.name}`),
    )
  }

  const importLegacy = async () => {
    if (!legacy) return
    const failures = await actions.importLegacy(legacy)
    await actions.loadMonth(month, { force: true })
    clearLegacy()
    setLegacy(null)
    if (failures === 0) toast.success(`Imported ${legacy.bills.length} bills`)
    else toast.error(`Imported with ${failures} ${failures === 1 ? 'item' : 'items'} that didn’t save`)
  }

  return (
    <div className="mx-auto flex max-w-[90rem] flex-col gap-5 [&>*]:min-w-0 px-4 py-6 md:px-8 md:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-heading text-4xl font-semibold tracking-tight md:text-5xl">{formatMonth(month)}</h1>
          <p className="mt-1 text-muted-foreground" aria-live="polite">
            {ready ? headline(occurrences, paidCount, next) : loading ? 'Loading bills…' : 'Bills unavailable'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <MonthSwitcher month={month} currentMonth={monthOf(today)} onChange={setMonth} />
          <Button disabled={!ready} onClick={() => setSheet({ open: true, bill: null })}>
            <Plus aria-hidden="true" />
            Add bill
          </Button>
        </div>
      </header>

      {showImport && (
        <ImportBanner
          count={legacy.bills.length}
          onImport={importLegacy}
          onDiscard={() => {
            clearLegacy()
            setLegacy(null)
          }}
        />
      )}

      {errored && loadError ? (
        <LoadErrorPanel error={loadError} onRetry={retry} />
      ) : loading ? (
        <BillsSkeleton />
      ) : bills.length === 0 ? (
        !showImport && <EmptyState onAdd={() => setSheet({ open: true, bill: null })} />
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
