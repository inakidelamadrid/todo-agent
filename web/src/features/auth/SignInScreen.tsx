import { SignIn } from '@clerk/react'
import { BrandMark } from '@/components/AppShell'
import { clerkAppearance } from './clerkAppearance'

export const SignInScreen = () => (
  <main className="grid min-h-dvh place-items-center bg-background px-4 py-10 text-foreground">
    <div className="flex w-full max-w-sm flex-col items-center gap-8">
      <div className="flex items-center gap-2.5">
        <BrandMark />
        <span className="label-caps text-lg tracking-[0.06em]">todo-agent</span>
      </div>
      <div className="text-center">
        <h1 className="font-heading text-4xl font-semibold tracking-[-0.025em]">Sign in</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">Private to its owner. Sign in to continue.</p>
      </div>
      <SignIn routing="hash" appearance={clerkAppearance} />
    </div>
  </main>
)
