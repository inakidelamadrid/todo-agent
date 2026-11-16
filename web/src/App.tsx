import { AppShell } from '@/components/AppShell'
import { Toaster } from '@/components/ui/sonner'
import { AccountControl } from '@/features/auth/AccountControl'
import { AuthGate } from '@/features/auth/AuthGate'
import { BillsMonthView } from '@/features/bills/components/BillsMonthView'
import { RailStatus } from '@/features/bills/components/RailStatus'

const App = () => (
  <>
    <AuthGate>
      <AppShell status={<RailStatus />} account={<AccountControl />}>
        <BillsMonthView />
      </AppShell>
    </AuthGate>
    <Toaster position="bottom-center" />
  </>
)

export default App
