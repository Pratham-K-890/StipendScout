import { XIcon } from 'lucide-react'
import type { ComponentType } from 'react'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'

interface ConfirmDeclineButtonProps {
  onConfirm: () => void
  disabled?: boolean
  label?: string
  title?: string
  description?: string
  confirmLabel?: string
  icon?: ComponentType<{ className?: string }>
}

export function ConfirmDeclineButton({
  onConfirm,
  disabled,
  label = 'Decline this listing',
  title = 'Decline this listing?',
  description = 'This removes the application record entirely — the listing itself stays in the database, so it can come back in a future scan if you change your mind, but any tailored draft here will be gone.',
  confirmLabel = 'Decline',
  icon: Icon = XIcon,
}: ConfirmDeclineButtonProps) {
  return (
    <AlertDialog>
      <AlertDialogTrigger
        render={
          <Button variant="destructive" size="lg" disabled={disabled}>
            <Icon /> {label}
          </Button>
        }
      />
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction variant="destructive" onClick={onConfirm}>
            {confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
