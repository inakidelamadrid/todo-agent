import { FlaskConical, ReceiptText } from 'lucide-react'
import { BillsMonthView } from '@/features/bills/components/BillsMonthView'
import { PlaygroundScreen } from '@/features/playground/PlaygroundScreen'
import type { ScreenDef } from '@/lib/screen'

/** Every screen, declared once. The first entry is the default. */
export const screens: readonly ScreenDef[] = [
  { id: 'bills', label: 'Bills', icon: <ReceiptText className="size-4" aria-hidden="true" />, render: () => <BillsMonthView /> },
  {
    id: 'playground',
    label: 'Playground',
    icon: <FlaskConical className="size-4" aria-hidden="true" />,
    adminOnly: true,
    render: () => <PlaygroundScreen />,
  },
]
