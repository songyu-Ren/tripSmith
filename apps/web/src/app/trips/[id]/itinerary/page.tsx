'use client'

import Link from 'next/link'
import { useParams, useSearchParams } from 'next/navigation'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ItineraryCreateResponse } from '@tripsmith/shared'

import { api } from '@/lib/api'
import { getApiBaseUrl } from '@/lib/env'

export default function TripItineraryPage() {
  const params = useParams<{ id: string }>()
  const sp = useSearchParams()
  const tripId = params.id
  const planIndex = Number(sp.get('plan') || '0')

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ItineraryCreateResponse | null>(null)

  const exportIcs = useMemo(() => {
    return `${getApiBaseUrl()}/api/trips/${tripId}/export/ics`
  }, [tripId])

  const exportMd = useMemo(() => {
    return `${getApiBaseUrl()}/api/trips/${tripId}/export/md`
  }, [tripId])

  const generate = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const it = await api().createItinerary(tripId, { plan_index: planIndex })
      setResult(it)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [tripId, planIndex])

  useEffect(() => {
    void generate()
  }, [generate])

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <div className="text-xs text-zinc-400">
          <Link className="hover:underline" href={`/trips/${tripId}`}>
            ← 返回方案
          </Link>
        </div>
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-lg font-semibold">逐日行程</h1>
          <button
            className="rounded-lg border border-zinc-700 bg-zinc-950/30 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800"
            onClick={generate}
            type="button"
          >
            重新生成
          </button>
        </div>
      </div>

      {loading ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-sm text-zinc-400">
          生成中…
        </div>
      ) : null}

      {error ? (
        <div className="rounded-xl border border-red-900/60 bg-red-950/40 p-4 text-sm text-red-200">
          {error}
        </div>
      ) : null}

      {result?.itinerary_json ? (
        <div className="space-y-4">
          {result.itinerary_json.days.map((day) => (
            <div key={day.date} className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
              <div className="text-sm font-semibold">{day.date}</div>
              <div className="mt-3 space-y-2">
                {day.items.map((item, idx) => (
                  <div
                    key={`${item.period}-${idx}`}
                    className="rounded-lg border border-zinc-800 bg-zinc-950/30 px-3 py-2"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="text-sm font-medium">{item.period}</div>
                      <div className="text-xs text-zinc-400">
                        通勤 {item.commute.minutes} 分钟 · 停留 {item.stay_minutes} 分钟
                      </div>
                    </div>
                    <div className="mt-1 text-sm text-zinc-200">{item.poi_name}</div>
                    <div className="mt-1 text-xs text-zinc-400">天气：{item.weather_summary}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : null}

      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
        <div className="text-sm font-semibold">导出</div>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          <a
            className="flex-1 rounded-lg bg-indigo-600 px-3 py-2 text-center text-sm font-medium hover:bg-indigo-500"
            href={exportIcs}
            target="_blank"
            rel="noreferrer"
          >
            导出 ICS
          </a>
          <a
            className="flex-1 rounded-lg border border-zinc-700 bg-zinc-950/30 px-3 py-2 text-center text-sm text-zinc-200 hover:bg-zinc-800"
            href={exportMd}
            target="_blank"
            rel="noreferrer"
          >
            导出 Markdown
          </a>
        </div>
        <div className="mt-2 text-xs text-zinc-500">
          导出接口需要已生成 itinerary。
        </div>
      </div>
    </div>
  )
}

