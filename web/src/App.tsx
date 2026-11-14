import { AppShell } from '@/components/AppShell'
import { Toaster } from '@/components/ui/sonner'
import { BillsMonthView } from '@/features/bills/components/BillsMonthView'
import { RailStatus } from '@/features/bills/components/RailStatus'

const App = () => (
  <AppShell status={<RailStatus />}>
    <BillsMonthView />
    <Toaster position="bottom-center" />
  </AppShell>
)

export default App
