import { AlertTriangleIcon, BanknoteIcon, ClockIcon, MapPinIcon } from 'lucide-react'

import type { JDSummary } from '@/api/types'
import { Card, CardContent } from '@/components/ui/card'

const ROLE_LABELS: Record<NonNullable<JDSummary['role_tier']>, string> = {
  backend: 'Backend',
  ml_data_science: 'ML / Data Science',
  ai_agent_llm: 'AI Agent / LLM',
}

function stipendLabel(summary: JDSummary): { text: string; tone: 'success' | 'destructive' | 'muted' } {
  if (summary.stipend_status === 'confirmed_ok' && summary.stipend_amount) {
    return { text: `₹${summary.stipend_amount.toLocaleString('en-IN')}/month`, tone: 'success' }
  }
  if (summary.stipend_status === 'confirmed_below_minimum' && summary.stipend_amount) {
    return { text: `₹${summary.stipend_amount.toLocaleString('en-IN')}/month (below ₹10k)`, tone: 'destructive' }
  }
  return { text: 'Not stated in listing', tone: 'muted' }
}

const TONE_CLASSES = {
  success: 'text-success',
  destructive: 'text-destructive',
  muted: 'text-muted-foreground',
}

function Fact({ icon: Icon, label, tone = 'muted' }: { icon: typeof BanknoteIcon; label: string; tone?: keyof typeof TONE_CLASSES }) {
  return (
    <div className={`flex items-center gap-1.5 text-sm ${TONE_CLASSES[tone]}`}>
      <Icon className="size-4 shrink-0" />
      <span className="tabular-nums-brand">{label}</span>
    </div>
  )
}

function BulletGroup({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div>
      <h3 className="mb-1.5 text-xs font-medium text-muted-foreground">{title}</h3>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-foreground">
            <span className="mr-1.5 text-muted-foreground">•</span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Every application in the tracker already passed the matcher's hard
 * filters (a failing listing never becomes an Application row) — this
 * makes that reasoning visible instead of a black-box "it matched", since
 * showing the actual rule+embedding checks is the real AI/ML work here,
 * not decoration. */
function MatchReasoning({ summary }: { summary: JDSummary }) {
  const stipend = stipendLabel(summary)
  const similarityPct = summary.role_similarity != null ? Math.round(summary.role_similarity * 100) : null
  return (
    <div className="border-t border-border pt-3">
      <h3 className="mb-2 text-xs font-medium text-muted-foreground">Why this matched</h3>
      <ul className="ledger space-y-1 text-xs">
        <li className={stipend.tone === 'destructive' ? 'text-destructive' : 'text-foreground'}>
          stipend — {stipend.text}
        </li>
        <li className="text-foreground">
          location — {summary.is_remote ? 'remote' : (summary.location ?? 'unstated')}
        </li>
        <li className="text-foreground">ppo — {summary.ppo_detected ? 'detected' : 'none detected'}</li>
        {summary.role_tier && (
          <li className="text-foreground">
            role — {ROLE_LABELS[summary.role_tier].toLowerCase()}
            {similarityPct != null && ` (${similarityPct}% embedding similarity to anchor)`}
          </li>
        )}
      </ul>
    </div>
  )
}

export function JDSummaryCard({ summary }: { summary: JDSummary }) {
  const stipend = stipendLabel(summary)
  const hasAiContent =
    summary.responsibilities.length > 0 ||
    summary.requirements.length > 0 ||
    summary.benefits.length > 0 ||
    summary.duration

  return (
    <Card className="mb-6">
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <Fact icon={BanknoteIcon} label={stipend.text} tone={stipend.tone} />
          <Fact icon={MapPinIcon} label={summary.is_remote ? 'Remote' : (summary.location ?? 'Unknown location')} />
          {summary.duration && <Fact icon={ClockIcon} label={summary.duration} />}
          {summary.role_tier && (
            <span className="border-l-2 border-l-primary bg-card px-2 py-0.5 text-xs font-medium text-foreground">
              {ROLE_LABELS[summary.role_tier]}
              {summary.role_similarity != null && (
                <span className="ledger text-muted-foreground"> · {Math.round(summary.role_similarity * 100)}%</span>
              )}
            </span>
          )}
          {summary.ppo_detected && (
            <span className="flex items-center gap-1 text-sm text-warning">
              <AlertTriangleIcon className="size-3.5" /> PPO-linked
            </span>
          )}
        </div>

        {hasAiContent && (
          <div className="grid grid-cols-1 gap-4 border-t border-border pt-4 sm:grid-cols-2">
            <BulletGroup title="Responsibilities" items={summary.responsibilities} />
            <BulletGroup title="Requirements" items={summary.requirements} />
            <BulletGroup title="Benefits" items={summary.benefits} />
          </div>
        )}

        <MatchReasoning summary={summary} />
      </CardContent>
    </Card>
  )
}
