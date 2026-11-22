import { CloudOff, FlaskConical, LayoutTemplate, ListTree, PowerOff, RotateCw, Route, Send, ShieldOff } from 'lucide-react'
import type { ComponentType, ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import type { PlaygroundGate } from './gate'

export type TabId = 'updates' | 'explain' | 'templates' | 'test-message'

type Icon = ComponentType<{ className?: string }>

const TABS: readonly { readonly id: TabId; readonly label: string; readonly icon: Icon; readonly blurb: string }[] = [
  { id: 'updates', label: 'Updates', icon: ListTree, blurb: 'The last updates the bot received, with the route each one took.' },
  { id: 'explain', label: 'Explain', icon: Route, blurb: 'Compose an update and see every router step, without running anything.' },
  { id: 'templates', label: 'Templates', icon: LayoutTemplate, blurb: 'Render a message template with sample data, buttons included.' },
  { id: 'test-message', label: 'Test message', icon: Send, blurb: 'Send one template to your own chat, marked as a test.' },
]

const Bar = ({ className }: { readonly className?: string }) => (
  <div className={cn('animate-pulse rounded-md bg-muted motion-reduce:animate-none', className)} />
)

const Page = ({ children }: { readonly children: ReactNode }) => (
  <div className="mx-auto flex max-w-[90rem] flex-col gap-5 px-4 py-6 md:px-8 md:py-8 [&>*]:min-w-0">{children}</div>
)

const Header = () => (
  <header className="flex flex-col gap-1">
    <h1 className="label-caps flex items-center gap-2.5 text-3xl md:text-4xl">
      <FlaskConical className="size-6 shrink-0 text-line-telecom md:size-7" aria-hidden="true" />
      Telegram playground
    </h1>
    <p className="text-muted-foreground">Development only. Nothing here reaches anyone but you.</p>
  </header>
)

/** One full-area state: icon in a ring, a title, a sentence, and an optional action. */
const GateState = ({ icon: Icon, tone, title, children, action }: {
  readonly icon: Icon
  readonly tone: 'muted' | 'bad'
  readonly title: string
  readonly children: ReactNode
  readonly action?: ReactNode
}) => (
  <section
    role={tone === 'bad' ? 'alert' : undefined}
    className="flex flex-col items-start gap-4 rounded-xl border bg-card px-4 py-8 md:flex-row md:items-center md:px-6"
  >
    <span
      className={cn(
        'grid size-11 shrink-0 place-items-center rounded-full border',
        tone === 'bad' ? 'border-overdue/60 text-overdue' : 'border-input text-muted-foreground',
      )}
    >
      <Icon className="size-5" aria-hidden="true" />
    </span>
    <div className="flex-1">
      <h2 className="font-heading text-xl font-semibold">{title}</h2>
      <div className="mt-1 max-w-[60ch] leading-relaxed text-muted-foreground">{children}</div>
    </div>
    {action}
  </section>
)

const Loading = () => (
  <div role="status" aria-label="Loading the playground" className="flex flex-col gap-5">
    <div className="flex gap-2 border-b pb-2">
      {[0, 1, 2, 3].map((i) => <Bar key={i} className="h-7 w-24" />)}
    </div>
    <div className="flex flex-col gap-3 rounded-xl border bg-card px-4 py-6 md:px-6">
      <Bar className="h-4 w-48" />
      {[0, 1, 2, 3].map((i) => <Bar key={i} className="h-9 w-full" />)}
    </div>
  </div>
)

const ComingSoon = ({ blurb }: { readonly blurb: string }) => (
  <div className="rounded-xl border border-dashed bg-card px-4 py-12 text-center md:px-6">
    <p className="font-heading text-xl font-semibold">Coming soon</p>
    <p className="mx-auto mt-1 max-w-[48ch] text-muted-foreground">{blurb}</p>
  </div>
)

const ToolTabs = ({ panels }: { readonly panels: Partial<Record<TabId, ReactNode>> }) => (
  <Tabs defaultValue="updates" className="gap-5">
    {/* The strip scrolls on its own at phone width; the page never does. */}
    <div className="-mx-4 overflow-x-auto border-b px-4 md:mx-0 md:px-0">
      <TabsList variant="line" aria-label="Playground tools" className="w-max gap-1 p-0 group-data-[orientation=horizontal]/tabs:h-10">
        {TABS.map(({ id, label, icon: Icon }) => (
          <TabsTrigger
            key={id}
            value={id}
            className="h-10 flex-none px-3 after:bg-line-streaming group-data-[orientation=horizontal]/tabs:after:bottom-0 focus-visible:border-transparent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset dark:data-active:text-foreground"
          >
            <Icon aria-hidden="true" />
            {label}
          </TabsTrigger>
        ))}
      </TabsList>
    </div>
    {TABS.map(({ id, blurb }) => (
      <TabsContent key={id} value={id} className="text-base focus-visible:ring-2 focus-visible:ring-ring/50 rounded-xl">
        {panels[id] ?? <ComingSoon blurb={blurb} />}
      </TabsContent>
    ))}
  </Tabs>
)

/** Presentational: the gate comes in as a prop, and nothing here fetches. */
export const PlaygroundShell = ({ gate, onRetry, panels = {} }: {
  readonly gate: PlaygroundGate
  readonly onRetry: () => void
  readonly panels?: Partial<Record<TabId, ReactNode>>
}) => (
  <Page>
    <Header />
    {gate === 'loading' && <Loading />}
    {gate === 'ready' && <ToolTabs panels={panels} />}
    {gate === 'off' && (
      <GateState icon={PowerOff} tone="muted" title="The playground is switched off">
        Set <code className="rounded-sm bg-muted px-1.5 py-0.5 font-mono text-sm text-foreground">TELEGRAM_PLAYGROUND_ENABLED</code>{' '}
        in <code className="rounded-sm bg-muted px-1.5 py-0.5 font-mono text-sm text-foreground">api/.env</code> and restart the API.
        It never runs in production.
      </GateState>
    )}
    {gate === 'not-admin' && (
      <GateState icon={ShieldOff} tone="muted" title="This area is for admins.">
        Your account can use the rest of todo-agent as usual.
      </GateState>
    )}
    {gate === 'error' && (
      <GateState
        icon={CloudOff}
        tone="bad"
        title="Can’t load the playground."
        action={
          <Button variant="outline" onClick={onRetry}>
            <RotateCw aria-hidden="true" />
            Try again
          </Button>
        }
      >
        Check that the API is running (make api-dev), then try again.
      </GateState>
    )}
  </Page>
)
