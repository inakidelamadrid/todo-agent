import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Popover, PopoverContent, PopoverDescription, PopoverTitle, PopoverTrigger } from '@/components/ui/popover'
import { formatMoney, toCents } from '../model/schedule'
import type { DateKey, Occurrence } from '../model/types'

interface Props {
  readonly occ: Occurrence
  readonly today: DateKey
  readonly emphasis: boolean
  readonly onConfirm: (actualCents: number, paidAt: DateKey) => void
}

const centsToInput = (cents: number): string => (cents / 100).toFixed(2)

export const MarkPaidPopover = ({ occ, today, emphasis, onConfirm }: Props) => {
  const [open, setOpen] = useState(false)
  const [amount, setAmount] = useState(centsToInput(occ.bill.estimatedCents))
  const [paidAt, setPaidAt] = useState(today)
  const cents = toCents(amount)
  const amountId = `paid-amount-${occ.bill.id}`
  const dateId = `paid-date-${occ.bill.id}`

  const reset = (next: boolean) => {
    setOpen(next)
    if (next) {
      setAmount(centsToInput(occ.bill.estimatedCents))
      setPaidAt(today)
    }
  }

  return (
    <Popover open={open} onOpenChange={reset}>
      <PopoverTrigger render={<Button variant={emphasis ? 'default' : 'outline'} size="sm" />}>Mark paid</PopoverTrigger>
      <PopoverContent align="end" className="w-80 gap-4 p-4">
        <div className="flex flex-col gap-1">
          <PopoverTitle className="font-heading text-lg font-semibold">Pay {occ.bill.name}</PopoverTitle>
          <PopoverDescription>
            Estimated {formatMoney(occ.bill.estimatedCents, occ.bill.currency)}. Enter what you actually paid.
          </PopoverDescription>
        </div>
        <form
          className="flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault()
            if (cents === null || !paidAt) return
            onConfirm(cents, paidAt)
            setOpen(false)
          }}
        >
          <div className="grid grid-cols-[1fr_auto] items-end gap-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor={amountId}>Amount paid</Label>
              <Input
                id={amountId}
                inputMode="decimal"
                autoFocus
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                aria-invalid={cents === null}
                aria-describedby={cents === null ? `${amountId}-error` : undefined}
                className="tabular"
              />
            </div>
            <span className="label-caps pb-2 text-sm text-muted-foreground">{occ.bill.currency}</span>
          </div>
          {cents === null && (
            <p id={`${amountId}-error`} className="text-sm text-destructive">
              Enter an amount like 649.00.
            </p>
          )}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor={dateId}>Paid on</Label>
            <Input id={dateId} type="date" value={paidAt} onChange={(e) => setPaidAt(e.target.value)} />
          </div>
          <Button type="submit" disabled={cents === null || !paidAt} className="mt-1">
            Mark paid
          </Button>
        </form>
      </PopoverContent>
    </Popover>
  )
}
