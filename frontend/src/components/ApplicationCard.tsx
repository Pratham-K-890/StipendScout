import { Link } from 'react-router-dom'

import type { ApplicationSummary } from '@/api/types'
import { STATUS } from '@/lib/status'

const DATE_FORMAT = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' })

export function ApplicationCard({ app }: { app: ApplicationSummary }) {
  const date = app.applied_at ?? app.created_at
  const dateLabel = app.applied_at ? 'applied' : 'added'
  const edge = STATUS[app.status].edge

  return (
    <Link
      to={`/applications/${app.id}`}
      className={`block border-l-2 bg-card px-3 py-2.5 transition-colors hover:bg-accent/40 ${edge}`}
    >
      <div className="line-clamp-2 font-serif text-[15px] leading-snug text-foreground">{app.listing_title}</div>
      <div className="truncate text-xs text-muted-foreground">{app.listing_company}</div>
      <div className="ledger mt-1.5 text-[10px] text-muted-foreground/70">
        {dateLabel} {DATE_FORMAT.format(new Date(date))}
      </div>
    </Link>
  )
}
