import { ArrowDownIcon, ArrowUpIcon } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import type { ApplicationSummary } from '@/api/types'
import { STATUS } from '@/lib/status'

type SortKey = 'date' | 'stipend' | 'status'

const DATE_FORMAT = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' })
const STATUS_RANK: Record<ApplicationSummary['status'], number> = {
  pending: 0,
  applied: 1,
  interview: 2,
  rejected: 3,
  stale: 4,
}

function sortValue(app: ApplicationSummary, key: SortKey): number {
  switch (key) {
    case 'date':
      return new Date(app.applied_at ?? app.created_at).getTime()
    case 'stipend':
      return app.stipend_amount ?? -1
    case 'status':
      return STATUS_RANK[app.status]
  }
}

function Th({
  label,
  sortKey,
  activeKey,
  dir,
  onSort,
}: {
  label: string
  sortKey: SortKey
  activeKey: SortKey
  dir: 'asc' | 'desc'
  onSort: (key: SortKey) => void
}) {
  const active = sortKey === activeKey
  return (
    <button
      type="button"
      onClick={() => onSort(sortKey)}
      className="flex items-center gap-1 text-left text-xs font-medium text-muted-foreground hover:text-foreground"
    >
      {label}
      {active && (dir === 'asc' ? <ArrowUpIcon className="size-3" /> : <ArrowDownIcon className="size-3" />)}
    </button>
  )
}

export function ListView({ applications }: { applications: ApplicationSummary[] }) {
  const [sortKey, setSortKey] = useState<SortKey>('date')
  const [dir, setDir] = useState<'asc' | 'desc'>('desc')

  function onSort(key: SortKey) {
    if (key === sortKey) {
      setDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setDir('desc')
    }
  }

  const sorted = [...applications].sort((a, b) => {
    const diff = sortValue(a, sortKey) - sortValue(b, sortKey)
    return dir === 'asc' ? diff : -diff
  })

  return (
    <div className="overflow-x-auto border-y border-border">
      <table className="w-full min-w-[640px] text-sm">
        <thead>
          <tr className="border-b border-border">
            <th className="w-8 py-2" />
            <th className="py-2 pr-4 text-left">
              <Th label="listing" sortKey="status" activeKey={sortKey} dir={dir} onSort={onSort} />
            </th>
            <th className="py-2 pr-4 text-left">
              <Th label="stipend" sortKey="stipend" activeKey={sortKey} dir={dir} onSort={onSort} />
            </th>
            <th className="py-2 pr-4 text-left">
              <Th label="date" sortKey="date" activeKey={sortKey} dir={dir} onSort={onSort} />
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((app) => {
            const meta = STATUS[app.status]
            const date = app.applied_at ?? app.created_at
            return (
              <tr key={app.id} className="border-b border-border last:border-b-0 hover:bg-accent/40">
                <td className="py-2 pl-1">
                  <span className={`block h-2 w-2 rounded-full ${meta.laneTop}`} title={meta.label} />
                </td>
                <td className="py-2 pr-4">
                  <Link to={`/applications/${app.id}`} className="block">
                    <div className="font-serif text-[15px] leading-snug text-foreground">{app.listing_title}</div>
                    <div className="text-xs text-muted-foreground">{app.listing_company}</div>
                  </Link>
                </td>
                <td className="ledger py-2 pr-4 text-foreground">
                  {app.stipend_amount != null ? `₹${app.stipend_amount.toLocaleString('en-IN')}` : '—'}
                </td>
                <td className="ledger py-2 pr-4 text-muted-foreground">{DATE_FORMAT.format(new Date(date))}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
