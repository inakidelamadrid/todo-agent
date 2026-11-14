import { formatMoney } from '../model/schedule'
import type { Currency, CurrencyTotals } from '../model/types'
import { CURRENCIES } from '../model/types'

interface Props {
  readonly totals: Readonly<Record<Currency, CurrencyTotals>>
}

const paidShare = (t: CurrencyTotals): number => (t.totalCents === 0 ? 0 : t.paidCents / t.totalCents)

const CurrencyBlock = ({ currency, totals }: { readonly currency: Currency; readonly totals: CurrencyTotals }) => (
  <section aria-label={`${currency} totals`} className="flex flex-col gap-3 px-5 py-4 md:px-6">
    <div className="flex items-baseline justify-between gap-4">
      <h2 className="label-caps text-sm text-muted-foreground">{currency} remaining</h2>
      <span className="text-sm text-muted-foreground tabular">
        Paid {formatMoney(totals.paidCents, currency)} of {formatMoney(totals.totalCents, currency)}
      </span>
    </div>
    <p className="font-heading text-4xl font-semibold leading-none tracking-tight tabular">
      {formatMoney(totals.remainingCents, currency)}
    </p>
    <div className="relative h-1.5 rounded-full bg-muted" aria-hidden="true">
      <div
        className="absolute inset-y-0 left-0 rounded-full bg-paid transition-[width] duration-300 ease-out"
        style={{ width: `${paidShare(totals) * 100}%` }}
      />
    </div>
  </section>
)

export const SummaryStrip = ({ totals }: Props) => (
  <div className="grid divide-y divide-border rounded-xl border bg-card md:grid-cols-2 md:divide-x md:divide-y-0">
    {CURRENCIES.map((c) => (
      <CurrencyBlock key={c} currency={c} totals={totals[c]} />
    ))}
  </div>
)
