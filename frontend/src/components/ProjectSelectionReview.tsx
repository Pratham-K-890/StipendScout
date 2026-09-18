import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckIcon, ExternalLinkIcon, GlobeIcon, LockIcon } from 'lucide-react'
import { useState } from 'react'

import { submitProjectSelection } from '@/api/client'
import type { ProjectSelectionReviewPayload } from '@/api/types'
import { ConfirmDeclineButton } from '@/components/ConfirmDeclineButton'
import { StepIndicator } from '@/components/StepIndicator'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { stripMarkdownNoise } from '@/lib/text'

export function ProjectSelectionReview({ payload }: { payload: ProjectSelectionReviewPayload }) {
  const queryClient = useQueryClient()
  const topRepoNames = payload.ranked_projects.slice(0, 3).map((r) => r.project.repo_name)
  const [selected, setSelected] = useState<Set<string>>(new Set(topRepoNames))

  const mutation = useMutation({
    mutationFn: ({ action }: { action: 'approve' | 'decline' }) =>
      submitProjectSelection(payload.application_id, action, Array.from(selected)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['application', payload.application_id] })
      queryClient.invalidateQueries({ queryKey: ['applications'] })
    },
  })

  function toggle(repoName: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(repoName)) next.delete(repoName)
      else next.add(repoName)
      return next
    })
  }

  return (
    <div>
      <StepIndicator step={1} label="Pick projects" />
      <h2 className="mb-1 text-lg font-semibold text-foreground">Review picked projects</h2>
      <p className="mb-4 text-sm text-muted-foreground">
        Ranked by fit with this posting. Pick which ones the tailored resume should draw from — the top 3 are
        checked by default.
      </p>

      <div className="space-y-3">
        {payload.ranked_projects.map((ranked) => {
          const snippet = ranked.project.description || stripMarkdownNoise(ranked.project.readme_excerpt)
          return (
            <label
              key={ranked.project.repo_name}
              className="flex cursor-pointer items-start gap-3 rounded-xl border border-border bg-card p-4 has-[:checked]:border-primary/40 has-[:checked]:bg-primary/5 hover:bg-secondary/50"
            >
              <Checkbox
                checked={selected.has(ranked.project.repo_name)}
                onCheckedChange={() => toggle(ranked.project.repo_name)}
                className="mt-1"
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-1.5 font-medium text-foreground">
                    {ranked.project.repo_name}
                    {ranked.project.is_private && <LockIcon className="size-3 text-muted-foreground" />}
                    {ranked.project.url && (
                      <a
                        href={ranked.project.url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-muted-foreground hover:text-primary"
                        aria-label={`Open ${ranked.project.repo_name} on GitHub`}
                      >
                        <ExternalLinkIcon className="size-3.5" />
                      </a>
                    )}
                    {ranked.project.deployed_url && (
                      <a
                        href={ranked.project.deployed_url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-muted-foreground hover:text-success"
                        aria-label={`Open live deployment of ${ranked.project.repo_name}`}
                        title="Live deployment"
                      >
                        <GlobeIcon className="size-3.5" />
                      </a>
                    )}
                  </span>
                  <span className="tabular-nums-brand shrink-0 rounded-full bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground">
                    {(ranked.similarity * 100).toFixed(0)}% match
                  </span>
                </div>
                {snippet && <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{snippet}</p>}
                {ranked.project.language && (
                  <span className="mt-2 inline-block rounded-full bg-accent px-2 py-0.5 text-xs text-accent-foreground">
                    {ranked.project.language}
                  </span>
                )}
              </div>
            </label>
          )
        })}
      </div>

      <div className="mt-6 flex gap-3">
        <Button size="lg" onClick={() => mutation.mutate({ action: 'approve' })} disabled={mutation.isPending || selected.size === 0}>
          <CheckIcon /> Approve selection
        </Button>
        <ConfirmDeclineButton onConfirm={() => mutation.mutate({ action: 'decline' })} disabled={mutation.isPending} />
      </div>
      {mutation.isError && <p className="mt-3 text-sm text-destructive">{mutation.error.message}</p>}
    </div>
  )
}
