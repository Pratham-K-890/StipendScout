import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

interface AppHeaderProps {
  eyebrow?: string
  title: string
  subtitle?: ReactNode
  back?: boolean
  actions?: ReactNode
}

export function AppHeader({ eyebrow, title, subtitle, back, actions }: AppHeaderProps) {
  return (
    <header className="border-b-2 border-primary bg-foreground text-background">
      <div className="mx-auto max-w-6xl px-6 py-7">
        {back && (
          <Link
            to="/"
            className="mb-4 inline-flex items-center gap-1 font-mono text-xs text-background/60 hover:text-background"
          >
            &lt; all applications
          </Link>
        )}
        <div className="flex items-start justify-between gap-6">
          <div className="min-w-0">
            {eyebrow && <div className="mb-1 font-mono text-xs text-background/55">{eyebrow}</div>}
            <h1 className="truncate text-2xl font-medium tracking-tight text-balance">{title}</h1>
            {subtitle && <div className="mt-1.5 text-sm text-background/70">{subtitle}</div>}
          </div>
          {actions && <div className="shrink-0">{actions}</div>}
        </div>
      </div>
    </header>
  )
}
