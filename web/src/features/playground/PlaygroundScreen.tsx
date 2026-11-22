import { useCallback, useEffect, useState } from 'react'
import { playgroundApi } from './api'
import { UpdateLogPanel } from './components/UpdateLogPanel'
import { filterSample, sampleUpdates } from './fixtures'
import { gateFromProbe, type PlaygroundGate } from './gate'
import { PlaygroundShell } from './PlaygroundShell'
import { TemplatesTab } from './TemplatesTab'
import { TestMessageTab } from './TestMessageTab'
import type { UpdateLogFilters } from './updateLog'

/** The one side effect here: ask the API whether the playground is on and this user is an admin. */
const usePlaygroundGate = () => {
  const [gate, setGate] = useState<PlaygroundGate>('loading')
  const probe = useCallback(() => playgroundApi.probe().then((result) => setGate(gateFromProbe(result))), [])
  useEffect(() => {
    void probe()
  }, [probe])
  const retry = () => {
    setGate('loading')
    void probe()
  }
  return { gate, retry }
}

export const PlaygroundScreen = () => {
  const { gate, retry } = usePlaygroundGate()
  const [now] = useState(() => new Date())
  const [filters, setFilters] = useState<UpdateLogFilters>({ status: 'all', route: '' })

  return (
    <PlaygroundShell
      gate={gate}
      onRetry={retry}
      panels={{
        // Sample rows until FE-024 wires the log to GET /admin/telegram/updates.
        updates: (
          <UpdateLogPanel
            items={filterSample(sampleUpdates(now), filters)}
            status="ready"
            filters={filters}
            onFiltersChange={setFilters}
            onRefresh={() => undefined}
            now={now}
          />
        ),
        templates: <TemplatesTab />,
        'test-message': <TestMessageTab />,
      }}
    />
  )
}
