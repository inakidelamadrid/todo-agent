import { daysBetween, dueDateFor, isDueInMonth, monthOf } from '../model/schedule'
import type { Bill, BillsData, DateKey, Payment } from '../model/types'

/** Sample data so the view is not empty on first run. Replace with your own bills. */
export const SAMPLE_BILLS: readonly Bill[] = [
  { id: 'cfe', name: 'CFE', note: 'Electricity · bimonthly reading', line: 'utilities', currency: 'MXN', estimatedCents: 124_000, dueDay: 8, recurrence: 'bimonthly', startMonth: '2026-01' },
  { id: 'agua', name: 'SACMEX', note: 'Water · bimonthly', line: 'utilities', currency: 'MXN', estimatedCents: 31_000, dueDay: 12, recurrence: 'bimonthly', startMonth: '2026-02' },
  { id: 'gas', name: 'Naturgy', note: 'Natural gas', line: 'utilities', currency: 'MXN', estimatedCents: 42_000, dueDay: 20, recurrence: 'monthly', startMonth: '2025-01' },
  { id: 'telmex', name: 'Telmex Infinitum', note: 'Home internet · 80 Mbps', line: 'telecom', currency: 'MXN', estimatedCents: 38_900, dueDay: 10, recurrence: 'monthly', startMonth: '2025-01' },
  { id: 'izzi', name: 'Izzi', note: 'TV + internet', line: 'telecom', currency: 'MXN', estimatedCents: 64_900, dueDay: 15, recurrence: 'monthly', startMonth: '2025-01' },
  { id: 'telcel', name: 'Telcel', note: 'Mobile plan', line: 'telecom', currency: 'MXN', estimatedCents: 49_900, dueDay: 18, recurrence: 'monthly', startMonth: '2025-01' },
  { id: 'netflix', name: 'Netflix', note: 'Standard plan', line: 'streaming', currency: 'MXN', estimatedCents: 29_900, dueDay: 5, recurrence: 'monthly', startMonth: '2025-01' },
  { id: 'spotify', name: 'Spotify', note: 'Family plan', line: 'streaming', currency: 'MXN', estimatedCents: 19_900, dueDay: 22, recurrence: 'monthly', startMonth: '2025-01' },
  { id: 'icloud', name: 'iCloud+', note: '2 TB storage', line: 'software', currency: 'USD', estimatedCents: 999, dueDay: 21, recurrence: 'monthly', startMonth: '2025-01' },
  { id: 'adobe', name: 'Adobe Photography', note: 'Lightroom + Photoshop', line: 'software', currency: 'USD', estimatedCents: 1_999, dueDay: 27, recurrence: 'monthly', startMonth: '2025-01' },
  { id: 'domain', name: 'Domain renewal', note: 'Personal domain · yearly', line: 'software', currency: 'USD', estimatedCents: 1_400, dueDay: 3, recurrence: 'yearly', startMonth: '2025-11' },
]

/** Bills already due before today in the current month start out paid, so every state shows up in the sample. */
export const seedData = (today: DateKey): BillsData => {
  const month = monthOf(today)
  const payments: readonly Payment[] = SAMPLE_BILLS.filter(
    (b) => b.id !== 'telmex' && isDueInMonth(b, month) && daysBetween(dueDateFor(b, month), today) > 0,
  ).map((b) => ({ billId: b.id, period: month, actualCents: b.estimatedCents, paidAt: dueDateFor(b, month) }))
  return { bills: SAMPLE_BILLS, payments }
}
