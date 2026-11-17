import { useClerk } from '@clerk/react'
import { LogOut } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { BrandMark } from '@/components/AppShell'
import { Button } from '@/components/ui/button'
import { useAuthStore } from './authStore'

export const NotAllowedScreen = () => {
  const { signOut } = useClerk()
  const reset = useAuthStore((s) => s.reset)
  const [signingOut, setSigningOut] = useState(false)

  const handleSignOut = async () => {
    setSigningOut(true)
    try {
      await signOut()
      reset()
    } catch {
      setSigningOut(false)
      toast.error("Couldn't sign out. Try again.")
    }
  }

  return (
    <main className="grid min-h-dvh place-items-center bg-background px-4 py-10 text-foreground">
      <div className="flex w-full max-w-sm flex-col items-center gap-6 text-center">
        <div className="flex items-center gap-2.5">
          <BrandMark />
          <span className="label-caps text-lg tracking-[0.06em]">todo-agent</span>
        </div>
        <div>
          <h1 className="font-heading text-3xl font-semibold tracking-[-0.025em]">
            This account isn&rsquo;t allowed to use todo-agent.
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            This workspace is private to its owner. Sign out to leave this session.
          </p>
        </div>
        <Button disabled={signingOut} onClick={handleSignOut}>
          <LogOut className="size-4" aria-hidden="true" />
          {signingOut ? 'Signing out…' : 'Sign out'}
        </Button>
      </div>
    </main>
  )
}
