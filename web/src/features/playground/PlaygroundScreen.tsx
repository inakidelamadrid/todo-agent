import { useState } from 'react'
import { UpdateLogPanel, type UpdateLogStatus } from './components/UpdateLogPanel'
import { filterSample, sampleUpdates } from './fixtures'
import { PlaygroundShell } from './PlaygroundShell'
import type { UpdateLogFilters } from './updateLog'

/** Change to look at each panel state; FE-021 and FE-024 replace these with the real probe and data. */
const FIXTURE_STATE: UpdateLogStatus = 'ready'

export const PlaygroundScreen = () => {
  const [now] = useState(() => new Date())
  const [filters, setFilters] = useState<UpdateLogFilters>({ status: 'all', route: '' })

  return (
    <PlaygroundShell
      gate="ready"
      onRetry={() => undefined}
      panels={{
        updates: (
          <UpdateLogPanel
            items={filterSample(sampleUpdates(now), filters)}
            status={FIXTURE_STATE}
            filters={filters}
            onFiltersChange={setFilters}
            onRefresh={() => undefined}
            now={now}
          />
        ),
      }}
    />
  )
}
