import { useClerk, useUser } from '@clerk/react'
import { LogOut } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { accountLabel } from './accountLabel'

export const AccountControl = () => {
  const { user } = useUser()
  const { signOut } = useClerk()
  const [signingOut, setSigningOut] = useState(false)
  const label = accountLabel(
    user ? { fullName: user.fullName, primaryEmail: user.primaryEmailAddress?.emailAddress } : null,
  )
  const actionLabel = signingOut ? 'Signing out…' : 'Sign out'

  const handleSignOut = async () => {
    setSigningOut(true)
    try {
      await signOut()
    } catch {
      setSigningOut(false)
      toast.error("Couldn't sign out. Try again.")
    }
  }

  return (
    <div className="flex items-center md:flex-col md:items-stretch md:gap-2.5 md:border-t md:border-white/15 md:pt-5">
      <p title={label} className="hidden truncate text-xs text-[#C3CDE8] md:block">
        {label}
      </p>
      <button
        type="button"
        disabled={signingOut}
        aria-label={actionLabel}
        title={label}
        onClick={handleSignOut}
        className="inline-flex size-8 items-center justify-center gap-2 rounded-lg border border-white/25 bg-transparent font-heading text-sm font-semibold uppercase tracking-[0.06em] text-rail-foreground transition-colors outline-none select-none hover:border-white/60 hover:bg-white/8 focus-visible:border-[#6E95FF] focus-visible:ring-3 focus-visible:ring-[#6E95FF]/50 active:translate-y-px disabled:pointer-events-none disabled:opacity-50 md:h-8 md:w-full md:justify-start md:px-2.5"
      >
        <LogOut className="size-4 shrink-0" aria-hidden="true" />
        <span className="hidden md:inline">{actionLabel}</span>
      </button>
    </div>
  )
}
