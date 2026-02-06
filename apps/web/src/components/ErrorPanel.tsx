'use client'

import { useMemo, useState } from 'react'
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

function getErrorCode(err: unknown): string | null {
  if (err instanceof ApiError) return err.errorCode || null
  return null
}

function getDetails(err: unknown): unknown {
  if (err instanceof ApiError) return err.data?.details
  return undefined
}

export function ErrorPanel({ error, onRetry }: Props) {
  const [retrying, setRetrying] = useState(false)
  const requestId = getRequestId(error)
  const errorCode = getErrorCode(error)
  const dev = process.env.NODE_ENV !== 'production'

  const copyText = useMemo(() => {
    if (error instanceof ApiError) {
      const payload: Record<string, unknown> = {
        status: error.status,
        error_code: error.errorCode,
        request_id: error.requestId,
        message: error.message
      }
      if (dev && error.data?.details != null) payload.details = error.data.details
      return JSON.stringify(payload, null, 2)
    }
    if (error instanceof Error) return `${error.name}: ${error.message}`
    return String(error)
  }, [dev, error])

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
    <div className="ts-card-strong text-sm" style={{ borderColor: 'rgba(248,113,113,0.35)' }}>
      <div className="space-y-2">
        <div className="text-red-200">{getMessage(error)}</div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-red-200/70">
          {errorCode ? <div>error_code: {errorCode}</div> : null}
          {requestId ? <div>request_id: {requestId}</div> : null}
        </div>
        {dev && getDetails(error) != null ? (
          <pre className="max-h-48 overflow-auto rounded-xl bg-black/30 p-3 text-xs text-red-100/80">
            {JSON.stringify(getDetails(error), null, 2)}
          </pre>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <button className="ts-btn-secondary text-xs" type="button" onClick={() => void navigator.clipboard.writeText(copyText)}>
          复制详情
        </button>
        <button
          className="ts-btn text-xs text-white"
          style={{ background: 'rgba(220,38,38,0.85)' }}
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
