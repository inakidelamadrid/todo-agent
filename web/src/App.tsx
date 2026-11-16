import { AppShell } from '@/components/AppShell'
import { Toaster } from '@/components/ui/sonner'
import { AuthGate } from '@/features/auth/AuthGate'
import { BillsMonthView } from '@/features/bills/components/BillsMonthView'
import { RailStatus } from '@/features/bills/components/RailStatus'

const App = () => (
  <AuthGate>
    <AppShell status={<RailStatus />}>
      <BillsMonthView />
      <Toaster position="bottom-center" />
    </AppShell>
  </AuthGate>
)

export default App
