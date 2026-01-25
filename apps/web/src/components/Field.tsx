'use client'

export function Field({
  label,
  children,
  hint
}: {
  label: string
  children: React.ReactNode
  hint?: string
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium text-zinc-200">{label}</label>
        {hint ? <div className="text-xs text-zinc-500">{hint}</div> : null}
      </div>
      {children}
    </div>
  )
}

