'use client'

import Link from 'next/link'
import { useParams, useSearchParams } from 'next/navigation'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ItineraryItem, ItineraryJson, JobDto } from '@tripsmith/shared'

import { api } from '@/lib/api'
import { getApiBaseUrl } from '@/lib/env'
import { ErrorPanel } from '@/components/ErrorPanel'
import { useJobPoll } from '@/lib/useJobPoll'

export default function TripItineraryPage() {
  const params = useParams<{ id: string }>()
  const sp = useSearchParams()
  const tripId = params.id
  const planIndex = Number(sp.get('plan') || '0')
  const planId = sp.get('planId')

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<unknown | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [result, setResult] = useState<{ itinerary_id: string; itinerary_json: ItineraryJson; itinerary_md: string } | null>(null)

  const { job, error: pollError } = useJobPoll(jobId, {
    onSucceeded: async (j: JobDto) => {
      const rj = (j.result_json || {}) as any
      if (rj.itinerary_json && rj.itinerary_md && rj.itinerary_id) {
        setResult({
          itinerary_id: String(rj.itinerary_id),
          itinerary_json: rj.itinerary_json as ItineraryJson,
          itinerary_md: String(rj.itinerary_md)
        })
      }
      setLoading(false)
    },
    onFailed: async (j: JobDto) => {
      const msg = j.error_message || j.message || 'Job failed'
      const next = j.next_action ? `\n\nNext: ${j.next_action}` : ''
      throw new Error(`${msg}${next}`)
    }
  })

  useEffect(() => {
    if (pollError) setError(pollError)
  }, [pollError])

  const exportIcs = useMemo(() => {
    return `${getApiBaseUrl()}/api/trips/${tripId}/export/ics`
  }, [tripId])

  const exportMd = useMemo(() => {
    return `${getApiBaseUrl()}/api/trips/${tripId}/export/md`
  }, [tripId])

  const generate = useCallback(async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const r = await api().createItinerary(tripId, { plan_index: planIndex, plan_id: planId })
      setJobId(r.job_id)
    } catch (e) {
      setError(e)
      setLoading(false)
    } finally {
      setLoading(false)
    }
  }, [tripId, planIndex, planId])

  useEffect(() => {
    void generate()
  }, [generate])

  const days = result?.itinerary_json?.days || []

  const periodLabels: Record<ItineraryItem['period'], string> = {
    morning: 'Morning',
    afternoon: 'Afternoon',
    evening: 'Evening'
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <div className="text-xs ts-muted">
          <Link className="hover:underline" href={`/trips/${tripId}`}>
            ← Back to plans
          </Link>
        </div>
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-lg font-semibold">Daily itinerary</h1>
          <button
            className="ts-btn-secondary"
            onClick={generate}
            type="button"
          >
            Regenerate
          </button>
        </div>
      </div>

      {loading ? (
        <div className="ts-card space-y-3">
          <div className="ts-skeleton h-5 w-28" />
          <div className="ts-skeleton h-4 w-full" />
          <div className="ts-skeleton h-4 w-3/4" />
        </div>
      ) : null}

      {job && job.status !== 'succeeded' ? (
        <div className="ts-card">
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm font-semibold">Job progress</div>
            <div className="text-xs ts-muted">{job.progress}%</div>
          </div>
          <div className="mt-2 h-2 w-full overflow-hidden rounded bg-zinc-800">
            <div className="h-2 bg-indigo-600" style={{ width: `${job.progress}%` }} />
          </div>
          <div className="mt-2 text-xs ts-muted">{job.message || job.stage}</div>
        </div>
      ) : null}

      {error ? (
        <ErrorPanel error={error} onRetry={generate} />
      ) : null}

      {days.length ? (
        <div className="space-y-4">
          {days.map((day) => {
            const byPeriod: Record<ItineraryItem['period'], ItineraryItem[]> = {
              morning: [],
              afternoon: [],
              evening: []
            }
            for (const item of day.items) {
              byPeriod[item.period].push(item)
            }

            return (
              <details key={day.date} className="ts-card" open>
                <summary className="cursor-pointer list-none select-none">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold">{day.date}</div>
                    <div className="text-xs ts-muted">{day.items.length} items</div>
                  </div>
                </summary>

                <div className="mt-4 space-y-3">
                  {(Object.keys(byPeriod) as ItineraryItem['period'][]).map((p) => (
                    <details key={p} className="rounded-2xl p-3" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }} open>
                      <summary className="cursor-pointer list-none select-none">
                        <div className="flex items-center justify-between gap-3">
                          <div className="text-sm font-semibold">{periodLabels[p]}</div>
                          <div className="text-xs ts-muted">{byPeriod[p].length ? `${byPeriod[p].length} items` : 'No plans'}</div>
                        </div>
                      </summary>

                      {byPeriod[p].length ? (
                        <div className="mt-3 space-y-2">
                          {byPeriod[p].map((item, idx) => (
                            <div key={`${item.period}-${idx}`} className="rounded-2xl p-3" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}>
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <div className="text-sm font-medium">{item.poi_name}</div>
                                <div className="text-xs ts-muted">
                                  Commute <span className="ts-mono">{item.commute.minutes}</span> min · Stay{' '}
                                  <span className="ts-mono">{item.stay_minutes}</span> min
                                </div>
                              </div>
                              <div className="mt-1 text-xs ts-muted">Weather: {item.weather_summary || 'N/A'}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="mt-2 text-sm ts-muted">No items for this time period.</div>
                      )}
                    </details>
                  ))}
                </div>
              </details>
            )
          })}
        </div>
      ) : result && !error ? (
        <div className="ts-card">
          <div className="text-sm">No itinerary content to display.</div>
          <div className="mt-1 text-xs ts-muted">Click “Regenerate” to try again.</div>
        </div>
      ) : null}

      <div className="ts-card">
        <div className="text-sm font-semibold">Export</div>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          <a
            className="ts-btn-primary flex-1"
            href={exportIcs}
            target="_blank"
            rel="noreferrer"
          >
            Export ICS
          </a>
          <a
            className="ts-btn-secondary flex-1"
            href={exportMd}
            target="_blank"
            rel="noreferrer"
          >
            Export Markdown
          </a>
        </div>
        <div className="mt-2 text-xs ts-muted">
          Export endpoints require an existing itinerary.
        </div>
      </div>
    </div>
  )
}

