import { FlaskConical, ReceiptText } from 'lucide-react'
import { AppShell, type NavItem } from '@/components/AppShell'
import { Toaster } from '@/components/ui/sonner'
import { AccountControl } from '@/features/auth/AccountControl'
import { AuthGate } from '@/features/auth/AuthGate'
import { isAdmin } from '@/features/auth/session'
import { useSessionStore } from '@/features/auth/useSessionStore'
import { BillsMonthView } from '@/features/bills/components/BillsMonthView'
import { RailStatus } from '@/features/bills/components/RailStatus'
import { PlaygroundScreen } from '@/features/playground/PlaygroundScreen'
import { type Screen, useHashScreen } from '@/lib/screen'

const navItems = (screen: Screen, admin: boolean): readonly NavItem[] => [
  { href: '#bills', label: 'Bills', icon: <ReceiptText className="size-4" aria-hidden="true" />, current: screen === 'bills' },
  ...(admin
    ? [{ href: '#playground', label: 'Playground', icon: <FlaskConical className="size-4" aria-hidden="true" />, current: screen === 'playground' }]
    : []),
]

const SignedInApp = () => {
  const admin = useSessionStore((s) => isAdmin(s.me))
  const screen = useHashScreen(admin)

  return (
    <AppShell items={navItems(screen, admin)} status={<RailStatus />} account={<AccountControl />}>
      {screen === 'playground' ? <PlaygroundScreen /> : <BillsMonthView />}
    </AppShell>
  )
}

const App = () => (
  <>
    <AuthGate>
      <SignedInApp />
    </AuthGate>
    <Toaster position="bottom-center" />
  </>
)

export default App
