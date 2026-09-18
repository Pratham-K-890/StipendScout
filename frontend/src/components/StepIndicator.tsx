export function StepIndicator({ step, label }: { step: 1 | 2; label: string }) {
  return (
    <div className="mb-2 text-xs font-semibold tracking-wide text-primary uppercase">
      Step {step} of 2 · {label}
    </div>
  )
}
