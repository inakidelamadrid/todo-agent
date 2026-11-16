export const MissingConfigScreen = () => (
  <main className="grid min-h-dvh place-items-center bg-background px-6 text-foreground">
    <div className="max-w-sm text-center">
      <h1 className="font-heading text-3xl font-semibold tracking-wide">Sign-in is not configured</h1>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
        Set <code className="font-mono text-foreground">VITE_CLERK_PUBLISHABLE_KEY</code> to your Clerk publishable
        key: copy <code className="font-mono text-foreground">web/.env.example</code> to{' '}
        <code className="font-mono text-foreground">web/.env.local</code>, fill it in and restart the dev server.
      </p>
    </div>
  </main>
)
