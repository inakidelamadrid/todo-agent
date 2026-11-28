import { FlaskConical, ListChecks, ReceiptText } from 'lucide-react'
import { BillsMonthView } from '@/features/bills/components/BillsMonthView'
import { PlaygroundScreen } from '@/features/playground/PlaygroundScreen'
import { TasksScreen } from '@/features/tasks/TasksScreen'
import type { ScreenDef } from '@/lib/screen'

/** Every screen, declared once. The first entry is the default. */
export const screens: readonly ScreenDef[] = [
  { id: 'bills', label: 'Bills', icon: <ReceiptText className="size-4" aria-hidden="true" />, render: () => <BillsMonthView /> },
  { id: 'tasks', label: 'Tasks', icon: <ListChecks className="size-4" aria-hidden="true" />, render: () => <TasksScreen /> },
  {
    id: 'playground',
    label: 'Playground',
    icon: <FlaskConical className="size-4" aria-hidden="true" />,
    adminOnly: true,
    render: () => <PlaygroundScreen />,
  },
]
