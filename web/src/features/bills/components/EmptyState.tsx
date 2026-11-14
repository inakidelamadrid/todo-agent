import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { LINE_META } from '../lines'
import { LINES } from '../model/types'

export const EmptyState = ({ onAdd }: { readonly onAdd: () => void }) => (
  <section className="flex flex-col items-center gap-6 rounded-xl border bg-card px-6 py-14 text-center">
    <svg viewBox="0 0 320 120" className="w-full max-w-sm" aria-hidden="true">
      {LINES.map((line, i) => (
        <line key={line} x1="12" x2="308" y1={18 + i * 28} y2={18 + i * 28} stroke={LINE_META[line].color} strokeWidth="6" strokeLinecap="round" opacity="0.35" />
      ))}
      <circle cx="160" cy="46" r="9" fill="var(--card)" stroke="var(--station)" strokeWidth="4" strokeDasharray="4 4" />
    </svg>
    <div className="max-w-md">
      <h2 className="font-heading text-2xl font-semibold">No bills on the network yet</h2>
      <p className="mt-2 text-muted-foreground">
        Add electricity, internet, phone and subscriptions. Each one becomes a station on its due day, and the totals
        show what is left to pay in pesos and dollars.
      </p>
    </div>
    <Button onClick={onAdd}>
      <Plus aria-hidden="true" />
      Add your first bill
    </Button>
  </section>
)
