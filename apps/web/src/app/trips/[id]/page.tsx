'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { PlansJson, TripGetResponse } from '@tripsmith/shared'

import { api } from '@/lib/api'
import { AlertModal } from '@/components/AlertModal'
import { PlanCard } from '@/components/PlanCard'

export default function TripResultsPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const tripId = params.id

  const [data, setData] = useState<TripGetResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [genLoading, setGenLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [alertOpen, setAlertOpen] = useState(false)

  const plans: PlansJson | null = useMemo(() => {
    return data?.latest_plans_json || null
  }, [data])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const d = await api().getTrip(tripId)
      setData(d)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [tripId])

  useEffect(() => {
    void load()
  }, [load])

  async function generatePlans() {
    setGenLoading(true)
    setError(null)
    try {
      await api().createPlan(tripId)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setGenLoading(false)
    }
  }

  async function goItinerary(planIndex: number) {
    router.push(`/trips/${tripId}/itinerary?plan=${planIndex}`)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="text-xs text-zinc-400">
            <Link className="hover:underline" href="/">
              ← 返回
            </Link>
          </div>
          <h1 className="text-lg font-semibold">方案结果</h1>
        </div>
        <button
          className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-40"
          onClick={generatePlans}
          disabled={genLoading}
          type="button"
        >
          {genLoading ? '生成中…' : '重新生成方案'}
        </button>
      </div>

      {loading ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-sm text-zinc-400">
          加载中…
        </div>
      ) : null}

      {error ? (
        <div className="rounded-xl border border-red-900/60 bg-red-950/40 p-4 text-sm text-red-200">
          {error}
        </div>
      ) : null}

      {data?.trip ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <div className="font-semibold">
              {data.trip.origin} → {data.trip.destination}
            </div>
            <div className="text-zinc-400">
              {data.trip.start_date} ~ {data.trip.end_date}
            </div>
            <div className="text-zinc-400">
              预算 {data.trip.budget_total} {data.trip.currency} · {data.trip.travelers} 人
            </div>
          </div>
        </div>
      ) : null}

      {!plans ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="text-sm text-zinc-300">暂无方案，点击“重新生成方案”开始。</div>
        </div>
      ) : (
        <div className="grid gap-4">
          {plans.options.slice(0, 3).map((opt, idx) => (
            <PlanCard
              key={opt.label}
              option={opt}
              onGenerate={() => void goItinerary(idx)}
              onAlert={() => setAlertOpen(true)}
            />
          ))}
        </div>
      )}

      <AlertModal open={alertOpen} onClose={() => setAlertOpen(false)} tripId={tripId} />
    </div>
  )
}

