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
      const msg = j.error_message || j.message || '任务失败'
      const next = j.next_action ? `\n\n下一步：${j.next_action}` : ''
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
        throw new Error('请先确认约束条件，再生成方案。')
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
              ← 返回
            </Link>
          </div>
          <h1 className="text-lg font-semibold">方案结果</h1>
        </div>
        <button
          className="ts-btn-primary"
          onClick={generatePlans}
          disabled={genLoading || !constraintsConfirmed}
          type="button"
        >
          {genLoading ? '生成中…' : constraintsConfirmed ? '重新生成方案' : '请先确认约束'}
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
            <div className="text-sm font-semibold">生成方案中…</div>
            <div className="text-xs ts-muted">{planJob?.progress ?? 0}%</div>
          </div>
          <div className="mt-2 h-2 w-full overflow-hidden rounded bg-zinc-800">
            <div className="h-2 bg-indigo-600" style={{ width: `${planJob?.progress ?? 0}%` }} />
          </div>
          <div className="mt-2 text-xs ts-muted">{planJob?.message || planJob?.stage || '排队中'}</div>
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
              预算 {data.trip.budget_total} {data.trip.currency} · {data.trip.travelers} 人
            </div>
          </div>
        </div>
      ) : null}

      {!constraintsConfirmed ? (
        <div className="ts-card">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold">确认约束</div>
              <div className="mt-1 text-xs ts-muted">
                系统会先生成可解释的约束条件，你可微调后确认，再开始生成方案。
              </div>
            </div>
            <button
              className="ts-btn-secondary"
              onClick={() => void generateConstraints()}
              disabled={constraintsBusy}
              type="button"
            >
              {constraintsBusy ? '处理中…' : constraints ? '重新生成约束' : '生成约束'}
            </button>
          </div>

          {constraints ? (
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label="节奏 (pace)">
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
              <Field label="每日步行容忍 (km)">
                <input
                  className="ts-input"
                  inputMode="decimal"
                  value={String(constraints.walking_tolerance_km_per_day)}
                  onChange={(e) =>
                    setConstraints({ ...constraints, walking_tolerance_km_per_day: Number(e.target.value) || 0 })
                  }
                />
              </Field>
              <Field label="每日活动上限 (小时)">
                <input
                  className="ts-input"
                  inputMode="decimal"
                  value={String(constraints.max_daily_activity_hours ?? 8)}
                  onChange={(e) =>
                    setConstraints({ ...constraints, max_daily_activity_hours: Number(e.target.value) || 0 })
                  }
                />
              </Field>
              <Field label="每日通勤上限 (小时)">
                <input
                  className="ts-input"
                  inputMode="decimal"
                  value={String(constraints.max_daily_commute_hours ?? 2)}
                  onChange={(e) =>
                    setConstraints({ ...constraints, max_daily_commute_hours: Number(e.target.value) || 0 })
                  }
                />
              </Field>
              <Field label="最大转机次数">
                <input
                  className="ts-input"
                  inputMode="numeric"
                  value={String(constraints.max_transfer_count)}
                  onChange={(e) =>
                    setConstraints({ ...constraints, max_transfer_count: Number(e.target.value) || 0 })
                  }
                />
              </Field>
              <Field label="酒店最低星级 (可选)">
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
              <Field label="允许红眼航班">
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
            <div className="mt-4 text-sm ts-muted">尚未生成约束。</div>
          )}

          <div className="mt-4">
            <button
              className="ts-btn-primary w-full"
              type="button"
              disabled={!constraints || constraintsBusy}
              onClick={() => void confirmConstraints()}
            >
              {constraintsBusy ? '提交中…' : '确认约束并继续'}
            </button>
          </div>
        </div>
      ) : null}

      {!plans ? (
        <div className="ts-card">
          <div className="text-sm">暂无方案，点击“重新生成方案”开始。</div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="ts-card">
            <div className="text-sm font-semibold">已保存的方案</div>
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
                      生成行程
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-2 text-sm ts-muted">尚未保存方案。你可以在下方选择并保存。</div>
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

