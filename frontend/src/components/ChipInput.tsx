import { XIcon } from 'lucide-react'
import { useState } from 'react'

import { Input } from '@/components/ui/input'

interface ChipInputProps {
  values: string[]
  onChange: (values: string[]) => void
  placeholder?: string
}

export function ChipInput({ values, onChange, placeholder }: ChipInputProps) {
  const [draft, setDraft] = useState('')

  function commit() {
    const trimmed = draft.trim()
    if (trimmed && !values.includes(trimmed)) onChange([...values, trimmed])
    setDraft('')
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5 rounded-lg border border-input p-2">
      {values.map((value) => (
        <span
          key={value}
          className="inline-flex items-center gap-1 rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
        >
          {value}
          <button
            type="button"
            onClick={() => onChange(values.filter((v) => v !== value))}
            aria-label={`Remove ${value}`}
            className="text-muted-foreground hover:text-destructive"
          >
            <XIcon className="size-3" />
          </button>
        </span>
      ))}
      <Input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault()
            commit()
          } else if (e.key === 'Backspace' && !draft && values.length > 0) {
            onChange(values.slice(0, -1))
          }
        }}
        onBlur={commit}
        placeholder={placeholder ?? 'Type and press Enter…'}
        className="h-6 min-w-32 flex-1 border-none px-1 shadow-none focus-visible:ring-0"
      />
    </div>
  )
}
