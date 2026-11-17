import { useAuth, useClerk } from '@clerk/react'
import { type ReactNode, useEffect } from 'react'
import { BrandMark } from '@/components/AppShell'
import { Button } from '@/components/ui/button'
import { useAuthStore } from './authStore'
import { resolveAuthView } from './authView'
import { NotAllowedScreen } from './NotAllowedScreen'
import { SignInScreen } from './SignInScreen'

const Centered = ({ children }: { readonly children: ReactNode }) => (
  <main className="grid min-h-dvh place-items-center bg-background px-6 text-foreground">
    <div className="flex max-w-sm flex-col items-center gap-4 text-center">{children}</div>
  </main>
)

export const AuthGate = ({ children }: { readonly children: ReactNode }) => {
  const { isLoaded, isSignedIn } = useAuth()
  const loadFailed = useClerk().status === 'error'
  const forbidden = useAuthStore((s) => s.forbidden)
  const reset = useAuthStore((s) => s.reset)
  const view = resolveAuthView({ isLoaded, isSignedIn, loadFailed, forbidden })

  useEffect(() => {
    if (isLoaded && !isSignedIn && forbidden) reset()
  }, [isLoaded, isSignedIn, forbidden, reset])

  if (view === 'signed-in') return children
  if (view === 'forbidden') return <NotAllowedScreen />
  if (view === 'loading')
    return (
      <Centered>
        <div role="status" aria-label="Loading" className="animate-pulse motion-reduce:animate-none">
          <BrandMark />
        </div>
      </Centered>
    )
  if (view === 'error')
    return (
      <Centered>
        <h1 className="font-heading text-2xl font-semibold">Can&rsquo;t reach sign-in right now</h1>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Your bills are safe. Check your connection and try again.
        </p>
        <Button onClick={() => window.location.reload()}>Try again</Button>
      </Centered>
    )
  return <SignInScreen />
}
