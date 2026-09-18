import { PlusIcon, XIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface BulletsEditorProps {
  bullets: string[]
  onChange: (bullets: string[]) => void
}

export function BulletsEditor({ bullets, onChange }: BulletsEditorProps) {
  function update(index: number, value: string) {
    onChange(bullets.map((b, i) => (i === index ? value : b)))
  }
  function remove(index: number) {
    onChange(bullets.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-1.5">
      <span className="text-xs font-medium text-muted-foreground">Bullets</span>
      {bullets.map((bullet, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <Input value={bullet} onChange={(e) => update(i, e.target.value)} placeholder="A specific, real accomplishment…" />
          <Button type="button" variant="ghost" size="icon-sm" onClick={() => remove(i)} aria-label="Remove bullet">
            <XIcon className="size-3.5" />
          </Button>
        </div>
      ))}
      <Button type="button" variant="outline" size="sm" onClick={() => onChange([...bullets, ''])}>
        <PlusIcon /> Add bullet
      </Button>
    </div>
  )
}
