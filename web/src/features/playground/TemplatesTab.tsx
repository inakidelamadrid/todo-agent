import { useEffect } from 'react'
import { TemplatePreviewPanel } from './components/TemplatePreviewPanel'
import { useTemplatesStore } from './useTemplatesStore'

export const TemplatesTab = () => {
  const s = useTemplatesStore()
  const load = useTemplatesStore((state) => state.load)

  useEffect(() => {
    void load()
  }, [load])

  return (
    <TemplatePreviewPanel
      templates={s.templates}
      status={s.status}
      loadError={s.error ?? undefined}
      selected={s.selected}
      data={s.data}
      fieldErrors={s.fieldErrors}
      preview={s.preview}
      previewStatus={s.previewStatus}
      previewError={s.previewError ?? undefined}
      onSelect={s.select}
      onFieldChange={s.setField}
      onPreview={() => void s.runPreview()}
      onRetry={() => void s.load({ force: true })}
    />
  )
}
