import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckIcon, DownloadIcon, TriangleAlertIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { resumePdfUrl, submitFinalApproval } from '@/api/client'
import type { TailoredBullet, TailoredResume } from '@/api/types'
import { ConfirmDeclineButton } from '@/components/ConfirmDeclineButton'
import { StepIndicator } from '@/components/StepIndicator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

const SECTION_TITLES: Record<TailoredBullet['source_type'], string> = {
  project: 'Projects',
  experience: 'Experience',
  hackathon: 'Hackathons',
  responsibility: 'Responsibilities',
}
const SECTION_ORDER: TailoredBullet['source_type'][] = ['project', 'experience', 'hackathon', 'responsibility']

const FLAG_HINT = "Not traceable to your source material or skill list — check before approving"

function groupBullets(bullets: TailoredBullet[]) {
  const groups = new Map<TailoredBullet['source_type'], TailoredBullet[]>()
  for (const bullet of bullets) {
    const list = groups.get(bullet.source_type) ?? []
    list.push(bullet)
    groups.set(bullet.source_type, list)
  }
  return groups
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// Grammarly-style inline flagging: underline the flagged phrase directly in
// the sentence it appears in, rather than a separate static list below —
// the point is to make the anti-fabrication signal legible at the exact
// spot the risk is, not as an afterthought.
function renderFlaggedText(text: string, flaggedTerms: string[]): ReactNode {
  if (flaggedTerms.length === 0) return text
  const sorted = [...flaggedTerms].sort((a, b) => b.length - a.length)
  const pattern = new RegExp(`(${sorted.map(escapeRegExp).join('|')})`, 'gi')
  const parts = text.split(pattern)
  return parts.map((part, i) =>
    i % 2 === 1 ? (
      <mark key={i} className="flag-mark cursor-help bg-transparent text-inherit" title={FLAG_HINT}>
        {part}
      </mark>
    ) : (
      <span key={i}>{part}</span>
    ),
  )
}

function SkillsSummary({ skills }: { skills: Record<string, string[]> }) {
  const entries = Object.entries(skills)
  if (entries.length === 0) return null
  return (
    <div className="mb-4">
      <h3 className="mb-1.5 text-xs font-medium text-muted-foreground">Skills this resume highlights</h3>
      <div className="space-y-0.5">
        {entries.map(([category, categorySkills]) => (
          <p key={category} className="text-sm text-foreground">
            <span className="font-medium">{category}:</span> {categorySkills.join(', ')}
          </p>
        ))}
      </div>
    </div>
  )
}

interface ResumeReviewProps {
  applicationId: string
  resume: TailoredResume
  coverLetterBody: string
  coverLetterFlaggedTerms?: string[]
  isPending: boolean
}

export function ResumeReview({
  applicationId,
  resume,
  coverLetterBody,
  coverLetterFlaggedTerms = [],
  isPending,
}: ResumeReviewProps) {
  const queryClient = useQueryClient()
  const grouped = groupBullets(resume.bullets)
  const totalFlags = resume.bullets.reduce((n, b) => n + b.flagged_terms.length, 0) + coverLetterFlaggedTerms.length

  const mutation = useMutation({
    mutationFn: (action: 'approve' | 'decline') => submitFinalApproval(applicationId, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['application', applicationId] })
      queryClient.invalidateQueries({ queryKey: ['applications'] })
    },
  })

  return (
    <div>
      {isPending && <StepIndicator step={2} label="Review resume" />}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">
          {isPending ? 'Review tailored resume' : 'Tailored resume'}
        </h2>
        <Button
          variant="outline"
          render={
            <a href={resumePdfUrl(applicationId)} target="_blank" rel="noreferrer">
              <DownloadIcon /> Download PDF
            </a>
          }
        />
      </div>

      {totalFlags > 0 && (
        <Alert className="mb-4 border-warning/40">
          <TriangleAlertIcon className="text-warning" />
          <AlertDescription className="text-warning">
            {totalFlags} phrase{totalFlags === 1 ? '' : 's'} below (underlined) couldn't be traced back to your
            source material or skill list — check them before approving.
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className="space-y-5">
          <SkillsSummary skills={resume.highlighted_skills} />
          {SECTION_ORDER.filter((type) => grouped.has(type)).map((type) => (
            <div key={type}>
              <h3 className="mb-2 text-xs font-medium text-muted-foreground">{SECTION_TITLES[type]}</h3>
              <ul className="space-y-2">
                {grouped.get(type)!.map((bullet, i) => (
                  <li key={i} className="doc-text text-sm text-foreground">
                    <span className="mr-1.5 font-sans text-muted-foreground">•</span>
                    {renderFlaggedText(bullet.text, bullet.flagged_terms)}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </CardContent>
      </Card>

      <h2 className="mt-6 mb-2 text-lg font-semibold text-foreground">Cover letter</h2>
      <Card>
        <CardContent className="doc-text whitespace-pre-wrap text-sm text-foreground">
          {renderFlaggedText(coverLetterBody, coverLetterFlaggedTerms)}
        </CardContent>
      </Card>

      {isPending && (
        <div className="mt-6 flex gap-3">
          <Button size="lg" onClick={() => mutation.mutate('approve')} disabled={mutation.isPending}>
            <CheckIcon /> Approve &amp; mark applied
          </Button>
          <ConfirmDeclineButton onConfirm={() => mutation.mutate('decline')} disabled={mutation.isPending} />
        </div>
      )}
      {mutation.isError && <p className="mt-3 text-sm text-destructive">{mutation.error.message}</p>}
    </div>
  )
}
