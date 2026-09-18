import type { ApplicationStats } from '@/api/types'

const ROLE_LABELS: Record<string, string> = {
  backend: 'Backend',
  ml_data_science: 'ML/DS',
  ai_agent_llm: 'AI Agent',
  unknown: 'Unclassified',
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <div className="ledger text-2xl text-foreground">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  )
}

export function StatsStrip({ stats }: { stats: ApplicationStats }) {
  const roleTiers = Object.entries(stats.role_tier_breakdown).filter(([, count]) => count > 0)

  return (
    <div className="mb-6 border-y border-border py-4">
      <div className="flex flex-wrap gap-x-10 gap-y-4">
        <Stat label="tracked" value={String(stats.total)} />
        <Stat
          label="response rate"
          value={stats.response_rate != null ? `${Math.round(stats.response_rate * 100)}%` : '—'}
        />
        <Stat
          label="avg stipend"
          value={stats.avg_stipend != null ? `₹${Math.round(stats.avg_stipend).toLocaleString('en-IN')}` : '—'}
        />
        {roleTiers.length > 0 && (
          <div className="min-w-0">
            <div className="flex items-baseline gap-4">
              {roleTiers.map(([tier, count]) => (
                <div key={tier} className="ledger text-2xl text-foreground">
                  {count}
                  <span className="ml-1 font-sans text-xs font-normal text-muted-foreground">
                    {ROLE_LABELS[tier] ?? tier}
                  </span>
                </div>
              ))}
            </div>
            <div className="text-xs text-muted-foreground">by role tier</div>
          </div>
        )}
      </div>
    </div>
  )
}
