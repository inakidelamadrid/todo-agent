import { AppShell } from '@/components/AppShell'
import { Toaster } from '@/components/ui/sonner'
import { AccountControl } from '@/features/auth/AccountControl'
import { AuthGate } from '@/features/auth/AuthGate'
import { isAdmin } from '@/features/auth/session'
import { useSessionStore } from '@/features/auth/useSessionStore'
import { RailStatus } from '@/features/bills/components/RailStatus'
import { useHashScreen, visibleNav } from '@/lib/screen'
import { screens } from '@/screens'

const SignedInApp = () => {
  const admin = useSessionStore((s) => isAdmin(s.me))
  const ctx = { isAdmin: admin, isDev: import.meta.env.DEV }
  const screen = useHashScreen(screens, ctx)

  return (
    <AppShell items={visibleNav(screens, ctx, screen.id)} status={<RailStatus />} account={<AccountControl />}>
      {screen.render()}
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
