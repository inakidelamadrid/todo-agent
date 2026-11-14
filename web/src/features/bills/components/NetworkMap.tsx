import { useLayoutEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { LINE_META } from '../lines'
import { amountOf, daysInMonth, formatDay, formatMoney, statusOf } from '../model/schedule'
import type { DateKey, Line, MonthKey, Occurrence, Payment, Status } from '../model/types'
import { LINES } from '../model/types'

interface Props {
  readonly month: MonthKey
  readonly today: DateKey
  readonly occurrences: readonly Occurrence[]
  readonly payments: readonly Payment[]
  readonly focusedLine: Line | null
  readonly onToggleLine: (line: Line) => void
  readonly onSelectBill: (billId: string) => void
}

const W = 1000
const PAD_X = 28
const TOP = 34
const ROW = 62
const H = TOP + ROW * LINES.length + 18

const dayOf = (date: DateKey): number => Number(date.slice(8, 10))
const rowY = (line: Line): number => TOP + ROW * LINES.indexOf(line) + ROW / 2

const STATUS_WORD: Readonly<Record<Status, string>> = {
  overdue: 'overdue',
  'due-soon': 'due soon',
  upcoming: 'upcoming',
  paid: 'paid',
}

/** Days shared by stations on two or more lines: drawn as interchange capsules. */
const interchanges = (occs: readonly Occurrence[]): readonly { day: number; lines: readonly Line[] }[] => {
  const byDay = occs.reduce<Readonly<Record<number, readonly Line[]>>>((acc, o) => {
    const day = dayOf(o.dueDate)
    const lines = acc[day] ?? []
    return lines.includes(o.bill.line) ? acc : { ...acc, [day]: [...lines, o.bill.line] }
  }, {})
  return Object.entries(byDay)
    .filter(([, lines]) => lines.length > 1)
    .map(([day, lines]) => ({ day: Number(day), lines }))
}

export const NetworkMap = ({ month, today, occurrences, payments, focusedLine, onToggleLine, onSelectBill }: Props) => {
  const days = daysInMonth(month)
  const x = (day: number): number => PAD_X + ((day - 1) / (days - 1)) * (W - PAD_X * 2)
  const isCurrentMonth = today.startsWith(month)
  const dim = (line: Line): boolean => focusedLine !== null && focusedLine !== line
  const ticks = Array.from({ length: days }, (_, i) => i + 1).filter((d) => d === 1 || d % 5 === 0 || d === days)
  const scroller = useRef<HTMLDivElement>(null)

  // On narrow screens the map scrolls; start with today a third of the way in so what is ahead stays visible.
  useLayoutEffect(() => {
    const el = scroller.current
    if (!el || el.scrollWidth <= el.clientWidth) return
    const scale = el.scrollWidth / W
    const todayLeft = isCurrentMonth ? x(dayOf(today)) * scale - el.clientWidth / 3 : 0
    // Never scroll an overdue station (or its label) out of view on the left.
    const firstOverdue = occurrences.find((o) => statusOf(o, payments, today) === 'overdue')
    const overdueLeft = firstOverdue ? x(dayOf(firstOverdue.dueDate)) * scale - 90 : Infinity
    el.scrollLeft = Math.max(0, Math.min(todayLeft, overdueLeft))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [month, today])

  return (
    <section aria-label="Month network" className="rounded-xl border bg-card">
      <div className="flex flex-wrap items-center gap-x-1 gap-y-2 border-b px-4 py-3 md:px-6">
        <h2 className="label-caps mr-3 text-sm text-muted-foreground">Lines</h2>
        {LINES.map((line) => (
          <button
            key={line}
            type="button"
            aria-pressed={focusedLine === line}
            onClick={() => onToggleLine(line)}
            className={cn(
              'flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm font-medium transition-[background-color,opacity] duration-200 outline-none hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring',
              focusedLine === line && 'bg-muted',
              dim(line) && 'opacity-55',
            )}
          >
            <span className="h-1 w-5 rounded-full" style={{ background: LINE_META[line].color }} aria-hidden="true" />
            {LINE_META[line].label}
          </button>
        ))}
      </div>

      <div
        ref={scroller}
        className="overflow-x-auto px-2 pb-2 max-md:[mask-image:linear-gradient(to_right,transparent,#000_1.5rem,#000_calc(100%-2.5rem),transparent)]"
      >
        <svg viewBox={`0 0 ${W} ${H}`} className="min-w-[60rem] w-full font-sans" role="img" aria-labelledby="network-desc">
          <desc id="network-desc">
            {occurrences.length} bills across the month, each a station on its due day, grouped in lines by category.
          </desc>

          {ticks.map((d) => (
            <g key={d}>
              <line x1={x(d)} x2={x(d)} y1={TOP - 8} y2={TOP} stroke="var(--muted-foreground)" strokeWidth="1.5" />
              <text x={x(d)} y={TOP - 14} textAnchor="middle" fontSize="13" fill="var(--muted-foreground)" className="tabular">
                {d}
              </text>
            </g>
          ))}

          {LINES.map((line) => (
            <line
              key={line}
              x1={PAD_X}
              x2={W - PAD_X}
              y1={rowY(line)}
              y2={rowY(line)}
              stroke={LINE_META[line].color}
              strokeWidth={focusedLine === line ? 10 : 7}
              strokeLinecap="round"
              opacity={dim(line) ? 0.2 : 1}
              className="transition-[opacity,stroke-width] duration-200"
            />
          ))}

          {LINES.flatMap((line) =>
            [PAD_X, W - PAD_X].map((cx) => (
              <line
                key={`${line}-${cx}`}
                x1={cx}
                x2={cx}
                y1={rowY(line) - 9}
                y2={rowY(line) + 9}
                stroke={LINE_META[line].color}
                strokeWidth="5"
                strokeLinecap="round"
                opacity={dim(line) ? 0.2 : 1}
                aria-hidden="true"
              />
            )),
          )}

          {isCurrentMonth && (
            <g aria-hidden="true">
              <line x1={x(dayOf(today))} x2={x(dayOf(today))} y1={TOP - 4} y2={H - 14} stroke="var(--foreground)" strokeWidth="2" />
              <rect x={x(dayOf(today)) - 26} y={H - 18} width="52" height="18" rx="4" fill="var(--foreground)" />
              <text x={x(dayOf(today))} y={H - 5} textAnchor="middle" fontSize="11" fontWeight="600" letterSpacing="1" fill="var(--card)">
                TODAY
              </text>
            </g>
          )}

          {interchanges(occurrences).map(({ day, lines }) => {
            const ys = lines.map(rowY)
            const top = Math.min(...ys) - 13
            return (
              <rect
                key={day}
                x={x(day) - 13}
                y={top}
                width="26"
                height={Math.max(...ys) - Math.min(...ys) + 26}
                rx="13"
                fill="var(--card)"
                stroke="var(--station)"
                strokeWidth="3"
                opacity={focusedLine && !lines.includes(focusedLine) ? 0.2 : 1}
              />
            )
          })}

          {occurrences.map((occ, i) => {
            const status = statusOf(occ, payments, today)
            const cx = x(dayOf(occ.dueDate))
            const cy = rowY(occ.bill.line)
            const sameLineIndex = occurrences.slice(0, i).filter((o) => o.bill.line === occ.bill.line).length
            const labelY = sameLineIndex % 2 === 0 ? cy - 17 : cy + 27
            const label = `${occ.bill.name}, ${formatDay(occ.dueDate)}, ${formatMoney(amountOf(occ, payments), occ.bill.currency)}, ${STATUS_WORD[status]}`
            return (
              <g
                key={occ.bill.id}
                role="button"
                tabIndex={0}
                aria-label={label}
                onClick={() => onSelectBill(occ.bill.id)}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), onSelectBill(occ.bill.id))}
                className="group cursor-pointer outline-none"
                opacity={dim(occ.bill.line) ? 0.25 : 1}
              >
                <title>{label}</title>
                {status === 'overdue' && (
                  <circle cx={cx} cy={cy} r="15" fill="none" stroke="var(--overdue)" strokeWidth="2" className="station-pulse" />
                )}
                <circle
                  cx={cx}
                  cy={cy}
                  r="9"
                  fill={status === 'paid' ? 'var(--station)' : 'var(--card)'}
                  stroke={status === 'overdue' ? 'var(--overdue)' : 'var(--station)'}
                  strokeWidth="4"
                  className="transition-[fill] duration-200 group-hover:stroke-[6] group-focus-visible:stroke-ring"
                />
                <text
                  x={cx}
                  y={labelY}
                  textAnchor="middle"
                  fontSize="14"
                  fontWeight="600"
                  letterSpacing="0.06em"
                  fontFamily="var(--font-display)"
                  fill={status === 'overdue' ? 'var(--overdue)' : 'var(--foreground)'}
                  className="pointer-events-none uppercase"
                >
                  {occ.bill.name.toUpperCase()}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    </section>
  )
}
