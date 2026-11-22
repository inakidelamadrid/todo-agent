import type { FieldErrors } from '@/lib/api'
import type { TemplateData, TemplateInfo } from './types'

export const MESSAGE_MAX = 4096

export const findTemplate = (templates: readonly TemplateInfo[], name: string | null): TemplateInfo | null =>
  templates.find((t) => t.name === name) ?? null

/** Pure: every field the template needs has a non-blank value. */
export const fieldsComplete = (template: TemplateInfo | null, data: TemplateData): boolean =>
  template !== null && template.fields.every((f) => (data[f] ?? '').trim() !== '')

/**
 * Pure: map an API refusal onto the template's fields. A 422 that names a field (in FastAPI's
 * `loc` list or in its message) becomes that field's inline error; otherwise there is none.
 */
export const fieldErrorsFrom = (
  error: { readonly status: number; readonly message: string; readonly fieldErrors?: FieldErrors },
  fields: readonly string[],
): FieldErrors => {
  if (error.status !== 422) return {}
  const fromLoc = Object.fromEntries(fields.filter((f) => error.fieldErrors?.[f]).map((f) => [f, error.fieldErrors![f]]))
  if (Object.keys(fromLoc).length > 0) return fromLoc
  const named = fields.find((f) => new RegExp(`\\b${f}\\b`).test(error.message))
  return named ? { [named]: error.message } : {}
}
