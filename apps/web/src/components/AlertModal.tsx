'use client'

import { useMemo, useState } from 'react'
import type { AlertCreateRequest } from '@tripsmith/shared'

import { api } from '@/lib/api'

export function AlertModal({
  open,
  onClose,
  tripId
}: {
  open: boolean
  onClose: () => void
  tripId: string
}) {
  const [type, setType] = useState<AlertCreateRequest['type']>('both')
  const [threshold, setThreshold] = useState('200')
  const [frequency, setFrequency] = useState('60')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const valid = useMemo(() => {
    const t = Number(threshold)
    const f = Number(frequency)
    return Number.isFinite(t) && t > 0 && Number.isFinite(f) && f > 0
  }, [threshold, frequency])

  if (!open) return null

  async function submit() {
    if (!valid) return
    setLoading(true)
    setError(null)
    try {
      await api().createAlert({
        trip_id: tripId,
        type,
        threshold: Number(threshold),
        frequency_minutes: Number(frequency)
      })
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-900 p-4 shadow-2xl">
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold">订阅价格提醒</div>
          <button
            className="rounded-md px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-800"
            onClick={onClose}
            type="button"
          >
            关闭
          </button>
        </div>
        <div className="mt-4 space-y-3">
          <div className="space-y-1">
            <div className="text-xs text-zinc-400">类型</div>
            <select
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              value={type}
              onChange={(e) => setType(e.target.value as AlertCreateRequest['type'])}
            >
              <option value="flight">机票</option>
              <option value="hotel">酒店</option>
              <option value="both">机票+酒店</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <div className="text-xs text-zinc-400">阈值（USD）</div>
              <input
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                inputMode="decimal"
              />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-zinc-400">频率（分钟）</div>
              <input
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
                inputMode="numeric"
              />
            </div>
          </div>
          {error ? (
            <div className="rounded-lg border border-red-900/60 bg-red-950/40 px-3 py-2 text-xs text-red-200">
              {error}
            </div>
          ) : null}
          <button
            className="w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-40"
            onClick={submit}
            disabled={!valid || loading}
            type="button"
          >
            {loading ? '提交中…' : '确认订阅'}
          </button>
        </div>
      </div>
    </div>
  )
}

