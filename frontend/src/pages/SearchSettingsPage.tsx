import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckIcon, SaveIcon } from 'lucide-react'
import { useState } from 'react'

import { getSearchSettings, saveSearchSettings } from '@/api/client'
import type { SearchSettings } from '@/api/types'
import { AppHeader } from '@/components/AppHeader'
import { ChipInput } from '@/components/ChipInput'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

export function SearchSettingsPage() {
  const { data, isLoading } = useQuery({ queryKey: ['search-settings'], queryFn: getSearchSettings })

  if (isLoading || !data) {
    return (
      <div className="min-h-screen bg-secondary/40">
        <div className="mx-auto max-w-3xl space-y-4 px-6 py-10">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-40 w-full rounded-xl" />
        </div>
      </div>
    )
  }

  return <SearchSettingsForm initialSettings={data} />
}

function SearchSettingsForm({ initialSettings }: { initialSettings: SearchSettings }) {
  const queryClient = useQueryClient()
  const [settings, setSettings] = useState(initialSettings)

  const mutation = useMutation({
    mutationFn: (s: SearchSettings) => saveSearchSettings(s),
    onSuccess: (saved) => queryClient.setQueryData(['search-settings'], saved),
  })

  return (
    <div className="min-h-screen bg-secondary/40">
      <AppHeader
        back
        eyebrow="Setup"
        title="Search Settings"
        subtitle="What Adzuna gets searched for, and what to filter out before it ever reaches the matcher."
        actions={
          <Button size="lg" onClick={() => mutation.mutate(settings)} disabled={mutation.isPending}>
            <SaveIcon /> {mutation.isPending ? 'Saving…' : 'Save'}
          </Button>
        }
      />

      <div className="mx-auto max-w-3xl space-y-6 px-6 py-6">
        {mutation.isSuccess && (
          <div className="flex items-center gap-2 rounded-lg border border-success/30 bg-success/10 px-4 py-3 text-sm text-success">
            <CheckIcon className="size-4" /> Search settings saved.
          </div>
        )}
        {mutation.isError && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            Save failed: {mutation.error.message}
          </div>
        )}

        <Card>
          <CardContent className="space-y-2">
            <h2 className="text-sm font-semibold text-foreground">Search queries</h2>
            <p className="text-xs text-muted-foreground">
              Each term is searched separately on Adzuna (Bengaluru) and the results are combined — targeted
              terms like "backend developer intern" surface far better matches than a single generic "intern"
              search.
            </p>
            <ChipInput
              values={settings.search_queries}
              onChange={(search_queries) => setSettings((prev) => ({ ...prev, search_queries }))}
              placeholder="Add a search term…"
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-2">
            <h2 className="text-sm font-semibold text-foreground">Exclude keywords</h2>
            <p className="text-xs text-muted-foreground">
              A listing is dropped before it reaches the matcher if any of these appear in its title or
              description — e.g. "sales", "marketing".
            </p>
            <ChipInput
              values={settings.exclude_keywords}
              onChange={(exclude_keywords) => setSettings((prev) => ({ ...prev, exclude_keywords }))}
              placeholder="Add a keyword to exclude…"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
