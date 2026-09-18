import { Badge } from '@/components/ui/badge'
import { STATUS } from '@/lib/status'
import type { ApplicationStatus } from '@/api/types'

export function StatusBadge({ status }: { status: ApplicationStatus }) {
  const meta = STATUS[status]
  const Icon = meta.icon
  return (
    <Badge className={meta.badge}>
      <Icon className="size-3" />
      {meta.label}
    </Badge>
  )
}
