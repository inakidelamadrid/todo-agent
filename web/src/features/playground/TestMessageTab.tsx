import { CheckCircle2, CircleAlert, RotateCw, Send } from 'lucide-react'
import { type ComponentType, useEffect, useState } from 'react'
import { toast } from 'sonner'
import {
  AlertDialog,
  AlertDialogClose,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { isApiError, playgroundApi } from './api'
import { TemplatePicker } from './components/TemplatePreviewPanel'
import { describeSendResult, type SendMessage, type SendOutcome } from './sendResult'
import { fieldErrorsFrom, fieldsComplete, findTemplate } from './templateForm'
import { useTemplatesStore } from './useTemplatesStore'

const TONE: Readonly<Record<SendMessage['tone'], { readonly icon: ComponentType<{ className?: string }>; readonly className: string }>> = {
  good: { icon: CheckCircle2, className: 'text-paid' },
  bad: { icon: CircleAlert, className: 'text-overdue' },
}

const ResultLine = ({ message }: { readonly message: SendMessage }) => {
  const { icon: Icon, className } = TONE[message.tone]
  return (
    <p role="status" className={cn('flex items-center gap-1.5 text-sm font-medium', className)}>
      <Icon className="size-4 shrink-0" aria-hidden="true" />
      {message.text}
    </p>
  )
}

const toOutcome = async (send: () => Promise<Awaited<ReturnType<typeof playgroundApi.sendTestMessage>>>): Promise<SendOutcome> => {
  try {
    return { ok: true, result: await send() }
  } catch (e) {
    return { ok: false, status: isApiError(e) ? e.status : 0, detail: e instanceof Error ? e.message : '' }
  }
}

/** Sends one template to the owner's own chat, after a confirmation. There is no recipient field. */
export const TestMessageTab = () => {
  const s = useTemplatesStore()
  const load = useTemplatesStore((state) => state.load)
  const [confirming, setConfirming] = useState(false)
  const [sending, setSending] = useState(false)
  const [message, setMessage] = useState<SendMessage | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Readonly<Record<string, string>>>({})

  useEffect(() => {
    void load()
  }, [load])

  const template = findTemplate(s.templates, s.selected)
  const canSend = s.status === 'ready' && fieldsComplete(template, s.data) && !sending

  const send = async () => {
    if (!s.selected) return
    setConfirming(false)
    setSending(true)
    setMessage(null)
    const outcome = await toOutcome(() => playgroundApi.sendTestMessage(s.selected!, s.data))
    const described = describeSendResult(outcome)
    setFieldErrors(outcome.ok ? {} : fieldErrorsFrom({ status: outcome.status, message: outcome.detail }, template?.fields ?? []))
    setMessage(described)
    setSending(false)
    if (outcome.ok) toast.success('Test message sent')
  }

  return (
    <section aria-labelledby="test-message-title" className="max-w-2xl rounded-xl border bg-card">
      <div className="border-b px-4 py-3 md:px-6">
        <h2 id="test-message-title" className="label-caps text-sm">Test message</h2>
        <p className="mt-0.5 text-sm text-muted-foreground">Sent right away to your own Telegram chat only. Up to 10 an hour.</p>
      </div>
      <div className="flex flex-col gap-5 px-4 py-4 md:px-6">
        {s.status === 'error' ? (
          <div role="alert" className="flex flex-col items-start gap-3">
            <p className="font-semibold">Can’t load templates</p>
            <p className="text-sm text-muted-foreground">{s.error ?? 'Check that the API is running, then try again.'}</p>
            <Button variant="outline" onClick={() => void s.load({ force: true })}>
              <RotateCw aria-hidden="true" />
              Try again
            </Button>
          </div>
        ) : s.status !== 'ready' ? (
          <div role="status" aria-label="Loading templates" className="flex flex-col gap-3">
            <div className="h-4 w-20 animate-pulse rounded-md bg-muted motion-reduce:animate-none" />
            <div className="h-8 w-full animate-pulse rounded-md bg-muted motion-reduce:animate-none" />
          </div>
        ) : (
          <>
            <TemplatePicker
              templates={s.templates}
              selected={s.selected}
              data={s.data}
              fieldErrors={fieldErrors}
              disabled={sending}
              idPrefix="test"
              onSelect={(name) => {
                s.select(name)
                setMessage(null)
                setFieldErrors({})
              }}
              onFieldChange={(name, value) => {
                s.setField(name, value)
                setFieldErrors((errors) => Object.fromEntries(Object.entries(errors).filter(([k]) => k !== name)))
              }}
            />
            <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
              <Button disabled={!canSend} onClick={() => setConfirming(true)}>
                <Send aria-hidden="true" />
                {sending ? 'Sending…' : 'Send test…'}
              </Button>
              {message && <ResultLine message={message} />}
            </div>
          </>
        )}
      </div>

      <AlertDialog open={confirming} onOpenChange={setConfirming}>
        <AlertDialogContent>
          <AlertDialogTitle>Send this to your own Telegram chat?</AlertDialogTitle>
          <AlertDialogDescription>
            The <code className="rounded-sm bg-muted px-1 py-px font-mono text-sm text-foreground">{s.selected}</code> template is sent now to
            the allowlisted chat. This can’t be undone.
          </AlertDialogDescription>
          <AlertDialogFooter>
            <AlertDialogClose render={<Button variant="outline" autoFocus />}>Cancel</AlertDialogClose>
            <Button onClick={() => void send()}>
              <Send aria-hidden="true" />
              Send
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  )
}
