'use client'

import { useState } from 'react'
import { ApiError } from '@tripsmith/shared'

type Props = {
  error: unknown
  onRetry: () => Promise<void>
}

function getMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message
  if (err instanceof Error) return err.message
  return String(err)
}

function getRequestId(err: unknown): string | null {
  if (err instanceof ApiError) return err.requestId || null
  return null
}

export function ErrorPanel({ error, onRetry }: Props) {
  const [retrying, setRetrying] = useState(false)
  const requestId = getRequestId(error)

  async function handleRetry() {
    if (retrying) return
    setRetrying(true)
    for (let i = 0; i <= 2; i += 1) {
      try {
        await onRetry()
        setRetrying(false)
        return
      } catch (e) {
        if (i === 2) break
        const delay = 250 * Math.pow(2, i)
        await new Promise((r) => setTimeout(r, delay))
      }
    }
    setRetrying(false)
  }

  return (
    <div className="rounded-xl border border-red-900/60 bg-red-950/40 p-4 text-sm text-red-200">
      <div className="space-y-1">
        <div>{getMessage(error)}</div>
        {requestId ? (
          <div className="text-xs text-red-200/70">request_id: {requestId}</div>
        ) : null}
      </div>
      <div className="mt-3">
        <button
          className="rounded-lg bg-red-700 px-3 py-2 text-xs font-medium hover:bg-red-600 disabled:opacity-40"
          type="button"
          disabled={retrying}
          onClick={() => void handleRetry()}
        >
          {retrying ? '重试中…' : '重试'}
        </button>
      </div>
    </div>
  )
}
