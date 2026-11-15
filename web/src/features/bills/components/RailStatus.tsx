import { formatDay, monthOf, occurrencesForMonth, relativeDue, statusOf, toDateKey } from '../model/schedule'
import { useBillsStore } from '../store/useBillsStore'

/** Network status for the rail: API offline, overdue count, the next bill to pay, or all clear. */
export const RailStatus = () => {
  const bills = useBillsStore((s) => s.bills)
  const payments = useBillsStore((s) => s.payments)
  const billsStatus = useBillsStore((s) => s.billsStatus)
  const loadError = useBillsStore((s) => s.loadError)
  const today = toDateKey(new Date())
  const currentMonthStatus = useBillsStore((s) => s.months[monthOf(today)])
  const occs = occurrencesForMonth(bills, monthOf(today))
  const overdue = occs.filter((o) => statusOf(o, payments, today) === 'overdue')
  const next = occs.find((o) => statusOf(o, payments, today) !== 'paid' && statusOf(o, payments, today) !== 'overdue')

  const [dot, title, detail] =
    billsStatus === 'error' || currentMonthStatus === 'error'
      ? ['var(--overdue)', loadError?.status === 401 ? 'Key rejected' : 'API offline', loadError?.status === 401 ? 'Check API_KEY in web/.env.local' : 'Run make api-dev, then retry']
      : billsStatus !== 'ready' || currentMonthStatus !== 'ready'
        ? ['var(--muted-foreground)', 'Connecting', 'Loading your bills…']
        : overdue.length > 0
          ? ['var(--overdue)', `${overdue.length} overdue`, `${overdue[0].bill.name}, ${relativeDue(overdue[0], today).toLowerCase()}`]
          : next
            ? ['var(--due-soon)', 'Bills ahead', `${next.bill.name}, ${formatDay(next.dueDate)}`]
            : ['var(--paid)', 'All paid', occs.length ? 'Nothing left this month' : 'No bills this month']

  return (
    <div role="status" className="flex flex-col gap-1">
      <p className="label-caps flex items-center gap-2 text-xs text-rail-foreground">
        <span className="size-2 rounded-full" style={{ background: dot }} aria-hidden="true" />
        {title}
      </p>
      <p className="text-sm text-[#C3CDE8]">{detail}</p>
    </div>
  )
}
