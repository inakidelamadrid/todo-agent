import { CloudOff, Eye, LayoutTemplate, RotateCw } from 'lucide-react'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { FieldErrors } from '@/lib/api'
import { cn } from '@/lib/utils'
import { parseTelegramHtml, type TgNode } from '../telegramHtml'
import { fieldsComplete, findTemplate, MESSAGE_MAX } from '../templateForm'
import type { TemplateData, TemplateInfo, TemplatePreview } from '../types'

export type LoadStatus = 'idle' | 'loading' | 'ready' | 'error'

export interface TemplatePickerProps {
  readonly templates: readonly TemplateInfo[]
  readonly selected: string | null
  readonly data: TemplateData
  readonly fieldErrors: FieldErrors
  readonly disabled?: boolean
  readonly idPrefix: string
  readonly onSelect: (name: string) => void
  readonly onFieldChange: (name: string, value: string) => void
}

/** Template select plus one input per field; shared by the Templates and Test message tabs. */
export const TemplatePicker = ({ templates, selected, data, fieldErrors, disabled, idPrefix, onSelect, onFieldChange }: TemplatePickerProps) => {
  const template = findTemplate(templates, selected)
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${idPrefix}-template`}>Template</Label>
        <Select
          value={selected}
          onValueChange={(v) => v && onSelect(v as string)}
          items={templates.map((t) => ({ value: t.name, label: t.name }))}
          disabled={disabled}
        >
          <SelectTrigger id={`${idPrefix}-template`} className="w-full font-mono">
            <SelectValue placeholder="Choose a template" />
          </SelectTrigger>
          <SelectContent>
            {templates.map((t) => (
              <SelectItem key={t.name} value={t.name} className="font-mono">
                {t.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      {template && template.fields.length === 0 && <p className="text-sm text-muted-foreground">No fields needed.</p>}
      {template?.fields.map((field) => {
        const id = `${idPrefix}-field-${field}`
        const error = fieldErrors[field]
        return (
          <div key={field} className="flex flex-col gap-1.5">
            <Label htmlFor={id} className="font-mono">{field}</Label>
            <Input
              id={id}
              value={data[field] ?? ''}
              disabled={disabled}
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? `${id}-error` : undefined}
              onChange={(e) => onFieldChange(field, e.target.value)}
            />
            {error && <p id={`${id}-error`} className="text-sm text-destructive">{error}</p>}
          </div>
        )
      })}
    </div>
  )
}

const NODE_CLASS: Readonly<Record<TgNode['kind'], string>> = {
  text: '',
  b: 'font-semibold',
  i: 'italic',
  code: 'rounded-sm bg-muted px-1 py-px font-mono text-[0.8125rem]',
}

/** Renders parsed nodes as plain React text: never markup from the server. */
export const ChatBubble = ({ html }: { readonly html: string }) => (
  <div className="flex flex-col items-start gap-1">
    <span className="label-caps text-[0.6875rem] text-muted-foreground">Bot</span>
    <p className="max-w-[34rem] rounded-2xl rounded-tl-md border bg-background px-4 py-2.5 leading-relaxed whitespace-pre-wrap break-words">
      {parseTelegramHtml(html).map((node, i) =>
        node.kind === 'text' ? <span key={i}>{node.text}</span> : node.kind === 'code' ? <code key={i} className={NODE_CLASS.code}>{node.text}</code> : <span key={i} className={NODE_CLASS[node.kind]}>{node.text}</span>,
      )}
    </p>
  </div>
)

const Bar = ({ className }: { readonly className?: string }) => (
  <div className={cn('animate-pulse rounded-md bg-muted motion-reduce:animate-none', className)} />
)

const Placeholder = ({ icon: Icon, children }: { readonly icon: typeof Eye; readonly children: ReactNode }) => (
  <div className="flex flex-col items-center gap-3 px-4 py-12 text-center text-muted-foreground">
    <span className="grid size-11 place-items-center rounded-full border border-input">
      <Icon className="size-5" aria-hidden="true" />
    </span>
    {children}
  </div>
)

const Result = ({ preview, status, error }: { readonly preview: TemplatePreview | null; readonly status: LoadStatus; readonly error?: string }) => {
  if (status === 'loading')
    return (
      <div role="status" aria-label="Rendering the preview" className="flex flex-col gap-3 p-4 md:p-6">
        <Bar className="h-3 w-10" />
        <Bar className="h-16 w-3/4 rounded-2xl" />
        <Bar className="mt-4 h-20 w-full" />
      </div>
    )
  if (status === 'error')
    return (
      <div role="alert" className="flex flex-col items-center gap-3 px-4 py-12 text-center">
        <span className="grid size-11 place-items-center rounded-full border border-overdue/60 text-overdue">
          <CloudOff className="size-5" aria-hidden="true" />
        </span>
        <p className="font-heading text-xl font-semibold">Can’t render this preview</p>
        <p className="max-w-[48ch] text-muted-foreground">{error ?? 'Check the fields and try again.'}</p>
      </div>
    )
  if (!preview)
    return (
      <Placeholder icon={Eye}>
        <p className="max-w-[40ch]">Pick a template, fill its fields and press <span className="label-caps text-foreground">Preview</span>.</p>
      </Placeholder>
    )
  return (
    <div className="flex flex-col gap-5 p-4 md:p-6" aria-live="polite">
      <ChatBubble html={preview.html} />
      <div className="flex flex-col gap-1.5">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="label-caps text-xs text-muted-foreground">HTML source</h3>
          <span className={cn('tabular text-xs', preview.length > MESSAGE_MAX ? 'text-overdue' : 'text-muted-foreground')}>
            {preview.length} / {MESSAGE_MAX}
          </span>
        </div>
        <pre className="max-h-64 overflow-auto rounded-lg border bg-muted/40 px-3 py-2.5 font-mono text-xs leading-relaxed whitespace-pre-wrap break-all">{preview.html}</pre>
      </div>
    </div>
  )
}

export interface TemplatePreviewPanelProps extends Omit<TemplatePickerProps, 'idPrefix' | 'disabled'> {
  readonly status: LoadStatus
  readonly loadError?: string
  readonly preview: TemplatePreview | null
  readonly previewStatus: LoadStatus
  readonly previewError?: string
  readonly onPreview: () => void
  readonly onRetry: () => void
}

/** Presentational: everything comes in as props, and nothing here fetches or stores. */
export const TemplatePreviewPanel = ({ status, loadError, preview, previewStatus, previewError, onPreview, onRetry, ...picker }: TemplatePreviewPanelProps) => {
  const template = findTemplate(picker.templates, picker.selected)
  const canPreview = status === 'ready' && fieldsComplete(template, picker.data) && previewStatus !== 'loading'
  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(18rem,24rem)_1fr] lg:items-start">
      <section aria-labelledby="template-form-title" className="rounded-xl border bg-card">
        <h2 id="template-form-title" className="label-caps border-b px-4 py-3 text-sm md:px-6">Compose</h2>
        <div className="px-4 py-4 md:px-6">
          {status === 'loading' || status === 'idle' ? (
            <div role="status" aria-label="Loading templates" className="flex flex-col gap-3">
              <Bar className="h-4 w-20" />
              <Bar className="h-8 w-full" />
            </div>
          ) : status === 'error' ? (
            <div role="alert" className="flex flex-col items-start gap-3">
              <p className="font-semibold">Can’t load templates</p>
              <p className="text-sm text-muted-foreground">{loadError ?? 'Check that the API is running, then try again.'}</p>
              <Button variant="outline" onClick={onRetry}>
                <RotateCw aria-hidden="true" />
                Try again
              </Button>
            </div>
          ) : picker.templates.length === 0 ? (
            <p className="text-sm text-muted-foreground">The API has no templates yet.</p>
          ) : (
            <form
              className="flex flex-col gap-5"
              onSubmit={(e) => {
                e.preventDefault()
                if (canPreview) onPreview()
              }}
            >
              <TemplatePicker {...picker} idPrefix="preview" disabled={previewStatus === 'loading'} />
              <Button type="submit" disabled={!canPreview} className="self-start">
                <Eye aria-hidden="true" />
                {previewStatus === 'loading' ? 'Rendering…' : 'Preview'}
              </Button>
            </form>
          )}
        </div>
      </section>
      <section aria-labelledby="template-result-title" className="min-w-0 rounded-xl border bg-card">
        <h2 id="template-result-title" className="label-caps flex items-center gap-2 border-b px-4 py-3 text-sm md:px-6">
          <LayoutTemplate className="size-4 text-muted-foreground" aria-hidden="true" />
          Preview
        </h2>
        <Result preview={preview} status={previewStatus} error={previewError} />
      </section>
    </div>
  )
}
