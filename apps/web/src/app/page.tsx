'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { TripCreateRequest } from '@tripsmith/shared'

import { api } from '@/lib/api'
import { Field } from '@/components/Field'

export default function HomePage() {
  const router = useRouter()
  const [origin, setOrigin] = useState('SFO')
  const [destination, setDestination] = useState('PAR')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [flexDays, setFlexDays] = useState('2')
  const [budget, setBudget] = useState('1800')
  const [travelers, setTravelers] = useState('1')
  const [prefs, setPrefs] = useState('balanced,walkable,food')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const valid = useMemo(() => {
    return (
      origin.trim().length > 0 &&
      destination.trim().length > 0 &&
      startDate.length === 10 &&
      endDate.length === 10 &&
      Number(budget) > 0 &&
      Number(travelers) > 0
    )
  }, [origin, destination, startDate, endDate, budget, travelers])

  async function submit() {
    if (!valid) return
    setLoading(true)
    setError(null)
    const payload: TripCreateRequest = {
      origin,
      destination,
      start_date: startDate,
      end_date: endDate,
      flexible_days: Number(flexDays) || 0,
      budget_total: Number(budget),
      currency: 'USD',
      travelers: Number(travelers),
      preferences: {
        tags: prefs
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean)
      }
    }
    try {
      const trip = await api().createTrip(payload)
      router.push(`/trips/${trip.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="space-y-2">
        <h1 className="text-lg font-semibold">开始规划你的旅行</h1>
        <p className="text-sm text-zinc-400">
          输入需求，生成 3 套方案（省钱/省时间/平衡），并可导出与订阅价格提醒。
        </p>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="出发地 (origin)">
            <input
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
            />
          </Field>
          <Field label="目的地 (destination)">
            <input
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
            />
          </Field>
          <Field label="开始日期">
            <input
              type="date"
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </Field>
          <Field label="结束日期">
            <input
              type="date"
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </Field>
          <Field label="弹性日期（±天）">
            <input
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              value={flexDays}
              onChange={(e) => setFlexDays(e.target.value)}
              inputMode="numeric"
            />
          </Field>
          <Field label="总预算（USD）">
            <input
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              inputMode="decimal"
            />
          </Field>
          <Field label="人数">
            <input
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              value={travelers}
              onChange={(e) => setTravelers(e.target.value)}
              inputMode="numeric"
            />
          </Field>
          <Field label="偏好（逗号分隔）" hint="示例：balanced,walkable,food">
            <input
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
              value={prefs}
              onChange={(e) => setPrefs(e.target.value)}
            />
          </Field>
        </div>

        {error ? (
          <div className="mt-4 rounded-lg border border-red-900/60 bg-red-950/40 px-3 py-2 text-xs text-red-200">
            {error}
          </div>
        ) : null}

        <button
          className="mt-4 w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-40"
          onClick={submit}
          disabled={!valid || loading}
          type="button"
        >
          {loading ? '创建中…' : '生成方案'}
        </button>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-sm text-zinc-300">
        <div className="font-medium">提示</div>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-zinc-400">
          <li>默认启用 Mock Providers，保证无任何 Key 也能跑通端到端。</li>
          <li>真实 POI/天气/路径 Provider 可在 `.env` 配置后启用。</li>
        </ul>
      </div>
    </div>
  )
}

