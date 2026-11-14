import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { addMonths, formatMonth } from '../model/schedule'
import type { MonthKey } from '../model/types'

interface Props {
  readonly month: MonthKey
  readonly currentMonth: MonthKey
  readonly onChange: (month: MonthKey) => void
}

export const MonthSwitcher = ({ month, currentMonth, onChange }: Props) => (
  <div className="flex items-center gap-1.5" role="group" aria-label="Month">
    <Button
      variant="outline"
      size="icon"
      aria-label={`Previous month, ${formatMonth(addMonths(month, -1))}`}
      onClick={() => onChange(addMonths(month, -1))}
    >
      <ChevronLeft />
    </Button>
    <Button variant="outline" disabled={month === currentMonth} onClick={() => onChange(currentMonth)}>
      This month
    </Button>
    <Button
      variant="outline"
      size="icon"
      aria-label={`Next month, ${formatMonth(addMonths(month, 1))}`}
      onClick={() => onChange(addMonths(month, 1))}
    >
      <ChevronRight />
    </Button>
  </div>
)
