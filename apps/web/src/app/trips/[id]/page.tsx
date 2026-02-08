'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { Constraints, PlansJson, SavedPlanDto, TripGetResponse } from '@tripsmith/shared'

import { api } from '@/lib/api'
import { AlertModal } from '@/components/AlertModal'
import { ErrorPanel } from '@/components/ErrorPanel'
import { Field } from '@/components/Field'
import { PlanCard } from '@/components/PlanCard'
import { useJobPoll } from '@/lib/useJobPoll'

export default function TripResultsPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const tripId = params.id

  const [data, setData] = useState<TripGetResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [genLoading, setGenLoading] = useState(false)
  const [error, setError] = useState<unknown | null>(null)
  const [alertOpen, setAlertOpen] = useState(false)
  const [constraints, setConstraints] = useState<Constraints | null>(null)
  const [constraintsConfirmed, setConstraintsConfirmed] = useState(false)
  const [constraintsBusy, setConstraintsBusy] = useState(false)
  const [planJobId, setPlanJobId] = useState<string | null>(null)
  const [savedPlans, setSavedPlans] = useState<SavedPlanDto[]>([])
  const [saveBusyIndex, setSaveBusyIndex] = useState<number | null>(null)

  const plans: PlansJson | null = useMemo(() => {
    return data?.latest_plans_json || null
  }, [data])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const d = await api().getTrip(tripId)
      setData(d)
      const c = await api().getConstraints(tripId)
      setConstraints(c.constraints)
      setConstraintsConfirmed(c.confirmed)
      const sp = await api().listSavedPlans(tripId)
      setSavedPlans(sp.saved_plans)
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }, [tripId])

  useEffect(() => {
    void load()
  }, [load])

  const { job: planJob, error: planJobPollError } = useJobPoll(planJobId, {
    onSucceeded: async () => {
      setPlanJobId(null)
      setGenLoading(false)
      await load()
    },
    onFailed: async (j) => {
      setPlanJobId(null)
      setGenLoading(false)
      const msg = j.error_message || j.message || 'Job failed'
      const next = j.next_action ? `\n\nNext: ${j.next_action}` : ''
      throw new Error(`${msg}${next}`)
    }
  })

  useEffect(() => {
    if (planJobPollError) setError(planJobPollError)
  }, [planJobPollError])

  async function generatePlans() {
    setGenLoading(true)
    setError(null)
    try {
      if (!constraintsConfirmed) {
        throw new Error('Please confirm constraints before generating plans.')
      }
      const r = await api().createPlan(tripId)
      setPlanJobId(r.job_id)
    } catch (e) {
      setGenLoading(false)
      setError(e)
    }
  }

  async function generateConstraints() {
    setConstraintsBusy(true)
    setError(null)
    try {
      const r = await api().generateConstraints(tripId)
      setConstraints(r.constraints)
      setConstraintsConfirmed(false)
    } catch (e) {
      setError(e)
    } finally {
      setConstraintsBusy(false)
    }
  }

  async function confirmConstraints() {
    if (!constraints) return
    setConstraintsBusy(true)
    setError(null)
    try {
      const r = await api().confirmConstraints(tripId, { constraints })
      setConstraints(r.constraints)
      setConstraintsConfirmed(r.confirmed)
    } catch (e) {
      setError(e)
    } finally {
      setConstraintsBusy(false)
    }
  }

  async function goItinerary(planIndex: number, planId?: string | null) {
    const qp = planId ? `&planId=${encodeURIComponent(planId)}` : ''
    router.push(`/trips/${tripId}/itinerary?plan=${planIndex}${qp}`)
  }

  async function saveSelectedPlan(planIndex: number) {
    if (!data?.latest_plan_id || !plans) return
    setSaveBusyIndex(planIndex)
    setError(null)
    try {
      const label = plans.options[planIndex]?.label || 'balanced'
      await api().savePlan(tripId, { plan_id: data.latest_plan_id, plan_index: planIndex, label })
      const sp = await api().listSavedPlans(tripId)
      setSavedPlans(sp.saved_plans)
    } catch (e) {
      setError(e)
    } finally {
      setSaveBusyIndex(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="text-xs ts-muted">
            <Link className="hover:underline" href="/">
              ← Back
            </Link>
          </div>
          <h1 className="text-lg font-semibold">Plan results</h1>
        </div>
        <button
          className="ts-btn-primary"
          onClick={generatePlans}
          disabled={genLoading || !constraintsConfirmed}
          type="button"
        >
          {genLoading ? 'Generating…' : constraintsConfirmed ? 'Regenerate plans' : 'Confirm constraints first'}
        </button>
      </div>

      {loading ? (
        <div className="ts-card space-y-3">
          <div className="ts-skeleton h-5 w-32" />
          <div className="ts-skeleton h-4 w-full" />
          <div className="ts-skeleton h-4 w-5/6" />
        </div>
      ) : null}

      {error ? (
        <ErrorPanel
          error={error}
          onRetry={async () => {
            await load()
          }}
        />
      ) : null}

      {planJobId ? (
        <div className="ts-card">
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm font-semibold">Generating plans…</div>
            <div className="text-xs ts-muted">{planJob?.progress ?? 0}%</div>
          </div>
          <div className="mt-2 h-2 w-full overflow-hidden rounded bg-zinc-800">
            <div className="h-2 bg-indigo-600" style={{ width: `${planJob?.progress ?? 0}%` }} />
          </div>
          <div className="mt-2 text-xs ts-muted">{planJob?.message || planJob?.stage || 'Queued'}</div>
        </div>
      ) : null}

      {data?.trip ? (
        <div className="ts-card">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <div className="font-semibold">
              {data.trip.origin} → {data.trip.destination}
            </div>
            <div className="ts-muted">
              {data.trip.start_date} ~ {data.trip.end_date}
            </div>
            <div className="ts-muted">
              Budget {data.trip.budget_total} {data.trip.currency} · {data.trip.travelers} travelers
            </div>
          </div>
        </div>
      ) : null}

      {!constraintsConfirmed ? (
        <div className="ts-card">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold">Confirm constraints</div>
              <div className="mt-1 text-xs ts-muted">
                Generate an explainable set of constraints, adjust if needed, then confirm to start plan generation.
              </div>
            </div>
            <button
              className="ts-btn-secondary"
              onClick={() => void generateConstraints()}
              disabled={constraintsBusy}
              type="button"
            >
              {constraintsBusy ? 'Working…' : constraints ? 'Regenerate constraints' : 'Generate constraints'}
            </button>
          </div>

          {constraints ? (
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label="Pace (pace)">
                <select
                  className="ts-input"
                  value={constraints.pace}
                  onChange={(e) =>
                    setConstraints({ ...constraints, pace: e.target.value as Constraints['pace'] })
                  }
                >
                  <option value="relaxed">relaxed</option>
                  <option value="balanced">balanced</option>
                  <option value="packed">packed</option>
                </select>
              </Field>
              <Field label="Daily walking tolerance (km)">
                <input
                  className="ts-input"
                  inputMode="decimal"
                  value={String(constraints.walking_tolerance_km_per_day)}
                  onChange={(e) =>
                    setConstraints({ ...constraints, walking_tolerance_km_per_day: Number(e.target.value) || 0 })
                  }
                />
              </Field>
              <Field label="Max daily activities (hours)">
                <input
                  className="ts-input"
                  inputMode="decimal"
                  value={String(constraints.max_daily_activity_hours ?? 8)}
                  onChange={(e) =>
                    setConstraints({ ...constraints, max_daily_activity_hours: Number(e.target.value) || 0 })
                  }
                />
              </Field>
              <Field label="Max daily commute (hours)">
                <input
                  className="ts-input"
                  inputMode="decimal"
                  value={String(constraints.max_daily_commute_hours ?? 2)}
                  onChange={(e) =>
                    setConstraints({ ...constraints, max_daily_commute_hours: Number(e.target.value) || 0 })
                  }
                />
              </Field>
              <Field label="Max transfers">
                <input
                  className="ts-input"
                  inputMode="numeric"
                  value={String(constraints.max_transfer_count)}
                  onChange={(e) =>
                    setConstraints({ ...constraints, max_transfer_count: Number(e.target.value) || 0 })
                  }
                />
              </Field>
              <Field label="Min hotel stars (optional)">
                <input
                  className="ts-input"
                  inputMode="numeric"
                  value={constraints.hotel_star_min == null ? '' : String(constraints.hotel_star_min)}
                  onChange={(e) =>
                    setConstraints({
                      ...constraints,
                      hotel_star_min: e.target.value ? Number(e.target.value) : null
                    })
                  }
                />
              </Field>
              <Field label="Allow red-eye flights">
                <label className="flex items-center gap-2 text-sm text-zinc-200">
                  <input
                    type="checkbox"
                    checked={constraints.night_flight_allowed}
                    onChange={(e) => setConstraints({ ...constraints, night_flight_allowed: e.target.checked })}
                  />
                  night_flight_allowed
                </label>
              </Field>
            </div>
          ) : (
            <div className="mt-4 text-sm ts-muted">Constraints have not been generated yet.</div>
          )}

          <div className="mt-4">
            <button
              className="ts-btn-primary w-full"
              type="button"
              disabled={!constraints || constraintsBusy}
              onClick={() => void confirmConstraints()}
            >
              {constraintsBusy ? 'Submitting…' : 'Confirm and continue'}
            </button>
          </div>
        </div>
      ) : null}

      {!plans ? (
        <div className="ts-card">
          <div className="text-sm">No plans yet. Click “Regenerate plans” to start.</div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="ts-card">
            <div className="text-sm font-semibold">Saved plans</div>
            {savedPlans.length ? (
              <div className="mt-3 grid gap-2">
                {savedPlans.slice(0, 6).map((sp) => (
                  <div
                    key={sp.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-xl px-3 py-2"
                    style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}
                  >
                    <div className="text-xs">
                      <span className="font-medium">{sp.label}</span>
                      <span className="ml-2 ts-muted">#{sp.plan_index + 1}</span>
                    </div>
                    <button className="ts-btn-primary px-3 py-1.5 text-xs" type="button" onClick={() => void goItinerary(sp.plan_index, sp.plan_id)}>
                      Generate itinerary
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-2 text-sm ts-muted">No saved plans yet. Pick one below and save it.</div>
            )}
          </div>

          <div className="grid gap-4">
            {plans.options.slice(0, 3).map((opt, idx) => (
              <PlanCard
                key={opt.label}
                option={opt}
                onGenerate={() => void goItinerary(idx, data?.latest_plan_id)}
                onSave={saveBusyIndex === idx ? undefined : () => void saveSelectedPlan(idx)}
                onAlert={() => setAlertOpen(true)}
              />
            ))}
          </div>
        </div>
      )}

      <AlertModal open={alertOpen} onClose={() => setAlertOpen(false)} tripId={tripId} />
    </div>
  )
}

