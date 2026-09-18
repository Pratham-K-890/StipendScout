import { AlertTriangleIcon, ClockIcon, MessagesSquareIcon, SendIcon, XCircleIcon } from 'lucide-react'

import type { ApplicationStatus } from '@/api/types'

interface StatusMeta {
  label: string
  icon: typeof ClockIcon
  /** badge background + text */
  badge: string
  /** left-edge bar on a lane row */
  edge: string
  /** lane header top stripe */
  laneTop: string
}

export const STATUS: Record<ApplicationStatus, StatusMeta> = {
  pending: {
    label: 'Pending',
    icon: ClockIcon,
    badge: 'bg-secondary text-secondary-foreground',
    edge: 'border-l-muted-foreground/50',
    laneTop: 'bg-muted-foreground/50',
  },
  applied: {
    label: 'Applied',
    icon: SendIcon,
    badge: 'bg-applied text-applied-foreground',
    edge: 'border-l-applied',
    laneTop: 'bg-applied',
  },
  interview: {
    label: 'Interview',
    icon: MessagesSquareIcon,
    badge: 'bg-success text-success-foreground',
    edge: 'border-l-success',
    laneTop: 'bg-success',
  },
  rejected: {
    label: 'Rejected',
    icon: XCircleIcon,
    badge: 'bg-destructive/15 text-destructive',
    edge: 'border-l-destructive',
    laneTop: 'bg-destructive',
  },
  stale: {
    label: 'Stale',
    icon: AlertTriangleIcon,
    badge: 'bg-warning/15 text-warning',
    edge: 'border-l-warning',
    laneTop: 'bg-warning',
  },
}
