import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { LINE_META, RECURRENCE_LABEL } from '../lines'
import { toCents } from '../model/schedule'
import type { Bill, Currency, Line, MonthKey, Recurrence } from '../model/types'
import { CURRENCIES, LINES } from '../model/types'

interface Props {
  readonly open: boolean
  readonly bill: Bill | null
  readonly defaultMonth: MonthKey
  readonly onOpenChange: (open: boolean) => void
  readonly onSave: (bill: Bill) => void
  readonly onDelete: (bill: Bill) => void
}

interface Draft {
  readonly name: string
  readonly note: string
  readonly line: Line
  readonly currency: Currency
  readonly amount: string
  readonly dueDay: string
  readonly recurrence: Recurrence
  readonly startMonth: MonthKey
}

const toDraft = (bill: Bill | null, month: MonthKey): Draft =>
  bill
    ? { ...bill, amount: (bill.estimatedCents / 100).toFixed(2), dueDay: String(bill.dueDay) }
    : { name: '', note: '', line: 'utilities', currency: 'MXN', amount: '', dueDay: '', recurrence: 'monthly', startMonth: month }

type Errors = Partial<Record<'name' | 'amount' | 'dueDay' | 'startMonth', string>>

const validate = (d: Draft): Errors => {
  const day = Number(d.dueDay)
  return {
    ...(d.name.trim() ? {} : { name: 'Give the bill a name, like “CFE” or “Netflix”.' }),
    ...(toCents(d.amount) !== null && d.amount.trim() ? {} : { amount: 'Enter the usual amount, like 649.00.' }),
    ...(Number.isInteger(day) && day >= 1 && day <= 31 ? {} : { dueDay: 'Pick a day from 1 to 31.' }),
    ...(/^\d{4}-\d{2}$/.test(d.startMonth) ? {} : { startMonth: 'Pick the first month it is due.' }),
  }
}

const fromDraft = (d: Draft, id: string): Bill => ({
  id,
  name: d.name.trim(),
  note: d.note.trim(),
  line: d.line,
  currency: d.currency,
  estimatedCents: toCents(d.amount) ?? 0,
  dueDay: Number(d.dueDay),
  recurrence: d.recurrence,
  startMonth: d.startMonth,
})

const Field = ({ id, label, error, children }: { id: string; label: string; error?: string; children: React.ReactNode }) => (
  <div className="flex flex-col gap-1.5">
    <Label htmlFor={id}>{label}</Label>
    {children}
    {error && (
      <p id={`${id}-error`} className="text-sm text-destructive">
        {error}
      </p>
    )}
  </div>
)

const FormBody = ({ bill, defaultMonth, onSave, onDelete, onCancel }: Omit<Props, 'open' | 'onOpenChange'> & { onCancel: () => void }) => {
  const [draft, setDraft] = useState<Draft>(() => toDraft(bill, defaultMonth))
  const [touched, setTouched] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const errors = touched ? validate(draft) : {}
  const set = <K extends keyof Draft>(key: K) => (value: Draft[K]) => setDraft((d) => ({ ...d, [key]: value }))
  const invalid = (key: keyof Errors) => ({ 'aria-invalid': Boolean(errors[key]), 'aria-describedby': errors[key] ? `bill-${key}-error` : undefined })

  return (
    <form
      className="flex min-h-0 flex-1 flex-col"
      noValidate
      onSubmit={(e) => {
        e.preventDefault()
        setTouched(true)
        if (Object.keys(validate(draft)).length === 0) onSave(fromDraft(draft, bill?.id ?? crypto.randomUUID()))
      }}
    >
      <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-4">
        <Field id="bill-name" label="Name" error={errors.name}>
          <Input id="bill-name" value={draft.name} onChange={(e) => set('name')(e.target.value)} placeholder="e.g. CFE" autoFocus {...invalid('name')} />
        </Field>
        <Field id="bill-note" label="Note (optional)">
          <Input id="bill-note" value={draft.note} onChange={(e) => set('note')(e.target.value)} placeholder="e.g. Electricity · account 1234" />
        </Field>
        <Field id="bill-line" label="Line">
          <Select value={draft.line} onValueChange={(v) => v && set('line')(v as Line)} items={LINES.map((l) => ({ value: l, label: LINE_META[l].label }))}>
            <SelectTrigger id="bill-line" className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              {LINES.map((l) => (
                <SelectItem key={l} value={l}>
                  <span className="h-1 w-4 rounded-full" style={{ background: LINE_META[l].color }} aria-hidden="true" />
                  {LINE_META[l].label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Field>
        <div className="grid grid-cols-[7rem_1fr] gap-3">
          <Field id="bill-currency" label="Currency">
            <Select value={draft.currency} onValueChange={(v) => v && set('currency')(v as Currency)} items={CURRENCIES.map((c) => ({ value: c, label: c }))}>
              <SelectTrigger id="bill-currency" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                {CURRENCIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
              </SelectContent>
            </Select>
          </Field>
          <Field id="bill-amount" label="Usual amount" error={errors.amount}>
            <Input id="bill-amount" inputMode="decimal" value={draft.amount} onChange={(e) => set('amount')(e.target.value)} placeholder="e.g. 649.00" className="tabular" {...invalid('amount')} />
          </Field>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Field id="bill-dueDay" label="Due day" error={errors.dueDay}>
            <Input id="bill-dueDay" type="number" min={1} max={31} value={draft.dueDay} onChange={(e) => set('dueDay')(e.target.value)} placeholder="1–31" className="tabular" {...invalid('dueDay')} />
          </Field>
          <Field id="bill-startMonth" label="First due" error={errors.startMonth}>
            <Input id="bill-startMonth" type="month" value={draft.startMonth} onChange={(e) => set('startMonth')(e.target.value)} {...invalid('startMonth')} />
          </Field>
        </div>
        <Field id="bill-recurrence" label="Repeats">
          <Select value={draft.recurrence} onValueChange={(v) => v && set('recurrence')(v as Recurrence)} items={Object.entries(RECURRENCE_LABEL).map(([value, label]) => ({ value, label }))}>
            <SelectTrigger id="bill-recurrence" className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              {Object.entries(RECURRENCE_LABEL).map(([value, label]) => <SelectItem key={value} value={value}>{label}</SelectItem>)}
            </SelectContent>
          </Select>
        </Field>
      </div>
      <SheetFooter className="border-t">
        <div className="flex gap-2">
          <Button type="button" variant="outline" className="flex-1" onClick={onCancel}>Cancel</Button>
          <Button type="submit" className="flex-1">{bill ? 'Save changes' : 'Add bill'}</Button>
        </div>
        {bill && (
          <Button
            type="button"
            variant={confirmDelete ? 'default' : 'ghost'}
            className={confirmDelete ? '' : 'text-destructive'}
            onClick={() => (confirmDelete ? onDelete(bill) : setConfirmDelete(true))}
          >
            {confirmDelete ? `Delete ${bill.name} and its payments` : 'Delete bill'}
          </Button>
        )}
      </SheetFooter>
    </form>
  )
}

export const BillFormSheet = ({ open, bill, defaultMonth, onOpenChange, onSave, onDelete }: Props) => (
  <Sheet open={open} onOpenChange={onOpenChange}>
    <SheetContent className="w-full gap-0 sm:max-w-md">
      <SheetHeader className="border-b">
        <SheetTitle className="font-heading text-2xl font-semibold">{bill ? `Edit ${bill.name}` : 'Add a bill'}</SheetTitle>
        <SheetDescription>It becomes a station on its line, on the day it is due.</SheetDescription>
      </SheetHeader>
      {open && (
        <FormBody
          key={bill?.id ?? 'new'}
          bill={bill}
          defaultMonth={defaultMonth}
          onSave={onSave}
          onDelete={onDelete}
          onCancel={() => onOpenChange(false)}
        />
      )}
    </SheetContent>
  </Sheet>
)
