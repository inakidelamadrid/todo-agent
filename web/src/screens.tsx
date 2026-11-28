import { FlaskConical, ListChecks, ReceiptText } from 'lucide-react'
import { BillsMonthView } from '@/features/bills/components/BillsMonthView'
import { TaskListPreview } from '@/features/tasks/components/TaskListPreview'
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
  { id: 'dev-tasks', label: 'Task list preview', icon: <ListChecks className="size-4" aria-hidden="true" />, devOnly: true, render: () => <TaskListPreview /> },
]
