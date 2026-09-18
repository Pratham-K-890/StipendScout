import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangleIcon, ChevronDownIcon, ExternalLinkIcon, MessagesSquareIcon, TrashIcon, XCircleIcon } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { ApiError, deleteApplication, getApplication, updateStatus } from '@/api/client'
import type { ApplicationStatus } from '@/api/types'
import { AppHeader } from '@/components/AppHeader'
import { ConfirmDeclineButton } from '@/components/ConfirmDeclineButton'
import { JDSummaryCard } from '@/components/JDSummaryCard'
import { ProjectSelectionReview } from '@/components/ProjectSelectionReview'
import { ResumeReview } from '@/components/ResumeReview'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Skeleton } from '@/components/ui/skeleton'

const MANUAL_STATUS_OPTIONS: { label: string; value: ApplicationStatus; icon: typeof MessagesSquareIcon }[] = [
  { label: 'Mark interview', value: 'interview', icon: MessagesSquareIcon },
  { label: 'Mark rejected', value: 'rejected', icon: XCircleIcon },
]

export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [jdOpen, setJdOpen] = useState(false)

  const {
    data: application,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['application', id],
    queryFn: () => getApplication(id!),
    enabled: !!id,
    retry: false,
  })

  const statusMutation = useMutation({
    mutationFn: (status: ApplicationStatus) => updateStatus(id!, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['application', id] })
      queryClient.invalidateQueries({ queryKey: ['applications'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteApplication(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      navigate('/')
    },
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="mx-auto max-w-3xl space-y-4 px-6 py-10">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-40 w-full" />
        </div>
      </div>
    )
  }

  if (isError || !application) {
    const message =
      error instanceof ApiError
        ? error.status === 404
          ? "This application doesn't exist — it may have been deleted or declined."
          : error.detail
        : "Couldn't load this application — check that the backend is running."
    return (
      <div className="min-h-screen bg-background">
        <AppHeader back eyebrow="stipendscout / applications" title="Something went wrong" />
        <div className="mx-auto max-w-3xl px-6 py-10">
          <div className="flex items-start gap-3 border-l-2 border-l-destructive bg-card px-4 py-3">
            <AlertTriangleIcon className="mt-0.5 size-4 shrink-0 text-destructive" />
            <div className="space-y-2">
              <p className="text-sm text-foreground">{message}</p>
              <Button size="sm" variant="outline" onClick={() => refetch()}>
                Try again
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const pending = application.pending_review
  const jdDescription =
    typeof application.jd_snapshot.description === 'string' ? application.jd_snapshot.description : null

  return (
    <div className="min-h-screen bg-background">
      <AppHeader
        back
        eyebrow={application.listing_company}
        title={application.listing_title}
        subtitle={
          <a
            href={application.listing_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 hover:text-background"
          >
            View original listing <ExternalLinkIcon className="size-3" />
          </a>
        }
        actions={<StatusBadge status={application.status} />}
      />

      <div className="mx-auto max-w-3xl px-6 py-6">
        {application.listing_summary && <JDSummaryCard summary={application.listing_summary} />}

        {jdDescription && (
          <Collapsible open={jdOpen} onOpenChange={setJdOpen} className="mb-6">
            <CollapsibleTrigger
              render={
                <button className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
                  <ChevronDownIcon className={`size-3.5 transition-transform ${jdOpen ? 'rotate-180' : ''}`} />
                  {jdOpen ? 'Hide full job description' : 'Show full job description'}
                </button>
              }
            />
            <CollapsibleContent>
              <p className="mt-3 border border-border bg-card p-4 text-sm whitespace-pre-wrap text-foreground">
                {jdDescription}
              </p>
            </CollapsibleContent>
          </Collapsible>
        )}

        {!jdDescription && <div className="mb-6" />}

        {pending?.type === 'project_selection' && <ProjectSelectionReview payload={pending} />}

        {pending?.type === 'final_approval' && (
          <ResumeReview
            applicationId={application.id}
            resume={pending.tailored_resume}
            coverLetterBody={pending.cover_letter.body}
            coverLetterFlaggedTerms={pending.cover_letter.flagged_terms}
            isPending
          />
        )}

        {!pending && application.tailored_resume && (
          <ResumeReview
            applicationId={application.id}
            resume={application.tailored_resume}
            coverLetterBody={application.tailored_cover_letter ?? ''}
            isPending={false}
          />
        )}

        {!pending && !application.tailored_resume && (
          <p className="text-sm text-muted-foreground">No tailored materials for this application yet.</p>
        )}

        {!pending && (
          <div className="mt-8 flex flex-wrap items-center gap-3 border-t border-border pt-6">
            {application.tailored_resume &&
              MANUAL_STATUS_OPTIONS.map((opt) => (
                <Button
                  key={opt.value}
                  variant="outline"
                  onClick={() => statusMutation.mutate(opt.value)}
                  disabled={statusMutation.isPending || application.status === opt.value}
                >
                  <opt.icon /> {opt.label}
                </Button>
              ))}
            <ConfirmDeclineButton
              label="Delete"
              title="Delete this application?"
              description="This permanently removes the application record and its tailored materials — the listing itself stays in the database, so it can come back in a future scan if you change your mind. This cannot be undone."
              confirmLabel="Delete"
              icon={TrashIcon}
              onConfirm={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
            />
          </div>
        )}
      </div>
    </div>
  )
}
