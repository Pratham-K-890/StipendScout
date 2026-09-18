import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { InboxIcon, LayoutGridIcon, ListIcon, RefreshCwIcon, SearchIcon, UserIcon } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { getApplicationStats, getProfile, listApplications, triggerScan } from '@/api/client'
import type { ApplicationStatus, ApplicationSummary } from '@/api/types'
import { AppHeader } from '@/components/AppHeader'
import { ApplicationCard } from '@/components/ApplicationCard'
import { ListView } from '@/components/ListView'
import { StatsStrip } from '@/components/StatsStrip'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { STATUS } from '@/lib/status'

const LANE_ORDER: ApplicationStatus[] = ['pending', 'applied', 'interview', 'rejected', 'stale']

type ViewMode = 'board' | 'list'

function loadViewMode(): ViewMode {
  try {
    const stored = localStorage.getItem('stipendscout:view-mode')
    return stored === 'list' ? 'list' : 'board'
  } catch {
    return 'board'
  }
}

export function ApplicationsListPage() {
  const queryClient = useQueryClient()
  const [viewMode, setViewMode] = useState<ViewMode>(loadViewMode)

  function setView(mode: ViewMode) {
    setViewMode(mode)
    try {
      localStorage.setItem('stipendscout:view-mode', mode)
    } catch {
      // per-viewer convenience only — fine if storage is blocked
    }
  }

  const { data: applications, isLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: () => listApplications(),
  })

  const { data: profile, isLoading: isProfileLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: getProfile,
  })

  const { data: stats } = useQuery({
    queryKey: ['applications', 'stats'],
    queryFn: getApplicationStats,
  })

  const scanMutation = useMutation({
    mutationFn: triggerScan,
    // Matches ['applications'] and ['applications', 'stats'] both — React
    // Query's invalidateQueries does prefix matching by default.
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['applications'] }),
  })

  const byStatus = useMemo(() => {
    const groups: Record<ApplicationStatus, ApplicationSummary[]> = {
      pending: [],
      applied: [],
      interview: [],
      rejected: [],
      stale: [],
    }
    for (const app of applications ?? []) groups[app.status].push(app)
    return groups
  }, [applications])

  const total = applications?.length ?? 0

  return (
    <div className="min-h-screen bg-background">
      <AppHeader
        eyebrow="stipendscout / applications"
        title="Applications"
        subtitle={
          total > 0
            ? `${total} tracked across five stages`
            : 'Internship applications, tracked and tailored.'
        }
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="lg"
              className="text-background hover:bg-background/10 hover:text-background"
              render={<Link to="/search-settings" />}
            >
              <SearchIcon /> Search
            </Button>
            <Button
              variant="ghost"
              size="lg"
              className="text-background hover:bg-background/10 hover:text-background"
              render={<Link to="/profile" />}
            >
              <UserIcon /> Profile
            </Button>
            <Button size="lg" onClick={() => scanMutation.mutate()} disabled={scanMutation.isPending}>
              <RefreshCwIcon className={scanMutation.isPending ? 'animate-spin' : ''} />
              {scanMutation.isPending ? 'Scanning…' : 'Run Scan'}
            </Button>
          </div>
        }
      />

      <div className="mx-auto max-w-6xl px-6 py-6">
        {stats && stats.total > 0 && <StatsStrip stats={stats} />}

        {!isProfileLoading && profile === null && (
          <div className="mb-6 flex items-center justify-between gap-4 rounded-lg border border-warning/30 bg-warning/10 px-4 py-3 text-sm text-foreground">
            <span>
              Your profile isn't set up yet — resume tailoring needs it (name, education, skills, past
              experience). Scanning and reviewing still work without it, but approving a project selection
              will fail until it's filled in.
            </span>
            <Button size="sm" variant="outline" className="shrink-0" render={<Link to="/profile" />}>
              <UserIcon /> Set up profile
            </Button>
          </div>
        )}

        <div aria-live="polite">
        {scanMutation.isSuccess && (
          <div className="mb-6 rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 text-sm text-foreground">
            Scanned {scanMutation.data.sources_scraped.join(', ')} — {scanMutation.data.new_applications_started}{' '}
            new application{scanMutation.data.new_applications_started === 1 ? '' : 's'} awaiting review.
          </div>
        )}
        {scanMutation.isError && (
          <div className="mb-6 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            Scan failed: {scanMutation.error.message}
          </div>
        )}
        </div>

        {isLoading && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-48 w-full rounded-xl" />
            ))}
          </div>
        )}

        {!isLoading && total === 0 && (
          <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border py-20 text-center">
            <InboxIcon className="size-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No applications yet. Run a scan to get started.</p>
          </div>
        )}

        {!isLoading && total > 0 && (
          <>
            <div className="mb-4 flex justify-end gap-1">
              <Button
                variant={viewMode === 'board' ? 'secondary' : 'ghost'}
                size="sm"
                onClick={() => setView('board')}
                aria-pressed={viewMode === 'board'}
              >
                <LayoutGridIcon /> Board
              </Button>
              <Button
                variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                size="sm"
                onClick={() => setView('list')}
                aria-pressed={viewMode === 'list'}
              >
                <ListIcon /> List
              </Button>
            </div>

            {viewMode === 'list' ? (
              <ListView applications={applications ?? []} />
            ) : (
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
                {LANE_ORDER.map((status) => {
                  const items = byStatus[status]
                  const meta = STATUS[status]
                  return (
                    <div key={status} className="min-w-0">
                      <div className={`h-1 w-9 rounded-full ${meta.laneTop}`} />
                      <div className="mt-2 mb-3 flex items-baseline gap-1.5">
                        <span className="text-sm font-medium text-foreground">{meta.label}</span>
                        <span className="ledger text-xs text-muted-foreground">{items.length}</span>
                      </div>
                      <div className="border-y border-border">
                        {items.length === 0 && (
                          <div className="px-3 py-6 text-center text-xs text-muted-foreground">None yet</div>
                        )}
                        {items.map((app, i) => (
                          <div key={app.id} className={i > 0 ? 'border-t border-border' : ''}>
                            <ApplicationCard app={app} />
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
