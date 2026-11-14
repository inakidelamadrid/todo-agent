import { AlertTriangle, Check, CircleDashed, Clock, Pencil, Undo2 } from 'lucide-react'
import type { ComponentType } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { LINE_META, STATUS_LABEL } from '../lines'
import { amountOf, findPayment, formatDay, formatMoney, formatMonth, relativeDue, type StatusGroup } from '../model/schedule'
import type { Bill, DateKey, MonthKey, Occurrence, Payment, Status } from '../model/types'
import { MarkPaidPopover } from './MarkPaidPopover'

interface Props {
  readonly month: MonthKey
  readonly today: DateKey
  readonly groups: readonly StatusGroup[]
  readonly payments: readonly Payment[]
  readonly highlightedId: string | null
  readonly onPay: (occ: Occurrence, actualCents: number, paidAt: DateKey) => void
  readonly onUndo: (occ: Occurrence) => void
  readonly onEdit: (bill: Bill) => void
}

const STATUS_STYLE: Readonly<Record<Status, { readonly icon: ComponentType<{ className?: string }>; readonly className: string }>> = {
  overdue: { icon: AlertTriangle, className: 'text-overdue' },
  'due-soon': { icon: Clock, className: 'text-due-soon' },
  upcoming: { icon: CircleDashed, className: 'text-muted-foreground' },
  paid: { icon: Check, className: 'text-paid' },
}

const StatusTag = ({ status, text }: { readonly status: Status; readonly text: string }) => {
  const { icon: Icon, className } = STATUS_STYLE[status]
  return (
    <span className={cn('inline-flex items-center gap-1.5 text-sm font-medium', className)}>
      <Icon className="size-4 shrink-0" aria-hidden="true" />
      {text}
    </span>
  )
}

const BillName = ({ bill }: { readonly bill: Bill }) => (
  <div className="flex min-w-0 items-center gap-3">
    <span
      className="h-1 w-5 shrink-0 rounded-full"
      style={{ background: LINE_META[bill.line].color }}
      title={LINE_META[bill.line].label}
    />
    <div className="min-w-0">
      <p className="truncate font-semibold">{bill.name}</p>
      <p className="truncate text-sm text-muted-foreground">{bill.note || LINE_META[bill.line].label}</p>
    </div>
  </div>
)

const Amount = ({ occ, payments }: { readonly occ: Occurrence; readonly payments: readonly Payment[] }) => {
  const cents = amountOf(occ, payments)
  const differs = findPayment(payments, occ.bill.id, occ.period) !== undefined && cents !== occ.bill.estimatedCents
  return (
    <div className="text-right tabular">
      <p className="font-semibold">
        <span className="label-caps mr-1.5 text-xs text-muted-foreground">{occ.bill.currency}</span>
        {formatMoney(cents, occ.bill.currency)}
      </p>
      {differs && <p className="text-xs text-muted-foreground">est. {formatMoney(occ.bill.estimatedCents, occ.bill.currency)}</p>}
    </div>
  )
}

const Actions = ({ occ, status, today, payments, onPay, onUndo, onEdit }: {
  readonly occ: Occurrence
  readonly status: Status
} & Pick<Props, 'today' | 'payments' | 'onPay' | 'onUndo' | 'onEdit'>) => {
  const payment = findPayment(payments, occ.bill.id, occ.period)
  return (
    <div className="flex items-center justify-end gap-1.5">
      {payment ? (
        <Button variant="ghost" size="sm" onClick={() => onUndo(occ)}>
          <Undo2 aria-hidden="true" />
          Undo
        </Button>
      ) : (
        <MarkPaidPopover occ={occ} today={today} emphasis={status === 'overdue'} onConfirm={(c, d) => onPay(occ, c, d)} />
      )}
      <Button variant="ghost" size="icon-sm" aria-label={`Edit ${occ.bill.name}`} onClick={() => onEdit(occ.bill)}>
        <Pencil />
      </Button>
    </div>
  )
}

const dueText = (occ: Occurrence, status: Status, today: DateKey, payments: readonly Payment[]): string => {
  const payment = findPayment(payments, occ.bill.id, occ.period)
  if (status === 'paid' && payment) return `Paid ${formatDay(payment.paidAt)}`
  return relativeDue(occ, today)
}

export const BillTable = ({ month, today, groups, payments, highlightedId, onPay, onUndo, onEdit }: Props) => {
  if (groups.length === 0) {
    return (
      <div className="rounded-xl border bg-card px-6 py-12 text-center">
        <p className="font-heading text-xl font-semibold">Nothing due in {formatMonth(month)}</p>
        <p className="mt-1 text-muted-foreground">Bills that repeat every 2 months or every year skip some months.</p>
      </div>
    )
  }

  const rowClass = (id: string) =>
    cn('transition-colors duration-500', highlightedId === id && 'bg-secondary')

  return (
    <div className="overflow-hidden rounded-xl border bg-card">
      {/* Desktop: table */}
      <table className="hidden w-full text-left md:table">
        <caption className="sr-only">Bills for {formatMonth(month)}</caption>
        <thead>
          <tr className="border-b">
            <th scope="col" className="label-caps px-6 py-3 text-xs font-semibold text-muted-foreground">Bill</th>
            <th scope="col" className="label-caps px-4 py-3 text-xs font-semibold text-muted-foreground">Due</th>
            <th scope="col" className="label-caps px-4 py-3 text-xs font-semibold text-muted-foreground">Status</th>
            <th scope="col" className="label-caps px-4 py-3 text-right text-xs font-semibold text-muted-foreground">Amount</th>
            <th scope="col" className="px-6 py-3"><span className="sr-only">Actions</span></th>
          </tr>
        </thead>
        {groups.map((g) => (
          <tbody key={g.status}>
            <tr>
              <th scope="rowgroup" colSpan={5} className="label-caps bg-muted/50 px-6 py-2 text-xs font-semibold text-muted-foreground">
                {STATUS_LABEL[g.status]} · {g.items.length}
              </th>
            </tr>
            {g.items.map((occ) => (
              <tr key={occ.bill.id} id={`bill-${occ.bill.id}`} tabIndex={-1} className={cn('border-t outline-none first:border-t-0', rowClass(occ.bill.id))}>
                <td className="max-w-0 px-6 py-3 w-[38%]"><BillName bill={occ.bill} /></td>
                <td className="px-4 py-3 tabular">{formatDay(occ.dueDate)}</td>
                <td className="px-4 py-3"><StatusTag status={g.status} text={dueText(occ, g.status, today, payments)} /></td>
                <td className="px-4 py-3"><Amount occ={occ} payments={payments} /></td>
                <td className="px-6 py-3">
                  <Actions occ={occ} status={g.status} today={today} payments={payments} onPay={onPay} onUndo={onUndo} onEdit={onEdit} />
                </td>
              </tr>
            ))}
          </tbody>
        ))}
      </table>

      {/* Mobile: list */}
      <div className="md:hidden">
        {groups.map((g) => (
          <section key={g.status} aria-label={STATUS_LABEL[g.status]}>
            <h3 className="label-caps bg-muted/50 px-4 py-2 text-xs text-muted-foreground">
              {STATUS_LABEL[g.status]} · {g.items.length}
            </h3>
            <ul>
              {g.items.map((occ) => (
                <li key={occ.bill.id} id={`bill-m-${occ.bill.id}`} className={cn('flex flex-col gap-3 border-t px-4 py-3 first:border-t-0', rowClass(occ.bill.id))}>
                  <div className="flex items-start justify-between gap-3">
                    <BillName bill={occ.bill} />
                    <Amount occ={occ} payments={payments} />
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <StatusTag status={g.status} text={g.status === "paid" ? dueText(occ, g.status, today, payments) : `${formatDay(occ.dueDate)} · ${dueText(occ, g.status, today, payments)}`} />
                    <Actions occ={occ} status={g.status} today={today} payments={payments} onPay={onPay} onUndo={onUndo} onEdit={onEdit} />
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  )
}
