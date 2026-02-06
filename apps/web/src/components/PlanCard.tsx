'use client'

import type { PlanOption } from '@tripsmith/shared'

export function PlanCard({
  option,
  onGenerate,
  onAlert,
  onSave
}: {
  option: PlanOption
  onGenerate: () => void
  onAlert: () => void
  onSave?: () => void
}) {
  return (
    <div className="ts-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{option.title}</div>
          <div className="mt-1 text-xs ts-muted">{option.explanation}</div>
        </div>
        <div className="text-right">
          <div className="text-sm font-semibold ts-mono">
            {Math.round(option.scorecard.total_cost)} {option.scorecard.currency}
          </div>
          <div className="text-xs ts-muted">总价</div>
        </div>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-5">
        <div className="rounded-xl px-3 py-2 text-xs text-zinc-200" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}>
          费用 {Math.round(option.scorecard.cost_score)}/100
        </div>
        <div className="rounded-xl px-3 py-2 text-xs text-zinc-200" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}>
          时间 {Math.round(option.scorecard.time_score)}/100
        </div>
        <div className="rounded-xl px-3 py-2 text-xs text-zinc-200" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}>
          舒适 {Math.round(option.scorecard.comfort_score)}/100
        </div>
        <div className="rounded-xl px-3 py-2 text-xs text-zinc-200" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}>
          通勤 {Math.round(option.scorecard.commute_score)}/100
        </div>
        <div className="rounded-xl px-3 py-2 text-xs text-zinc-200" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}>
          日负荷 {Math.round(option.scorecard.daily_load_score)}/100
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl p-3" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}>
          <div className="text-xs font-medium text-zinc-100">航班摘要</div>
          <div className="mt-2 space-y-1 text-xs text-zinc-200">
            <div>
              <span className="ts-mono">{option.flight.depart_at}</span> → <span className="ts-mono">{option.flight.arrive_at}</span>
            </div>
            <div>
              转机 {option.flight.stops} 次 · {option.flight.duration_minutes} 分钟 ·{' '}
              <span className="ts-mono">{Math.round(option.flight.price.amount)} {option.flight.price.currency}</span>
            </div>
          </div>
        </div>
        <div className="rounded-2xl p-3" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}>
          <div className="text-xs font-medium text-zinc-100">住宿摘要</div>
          <div className="mt-2 space-y-1 text-xs text-zinc-200">
            <div>{option.stay.name}</div>
            <div>
              {option.stay.area} ·{' '}
              <span className="ts-mono">
                {Math.round(option.stay.nightly_price.amount)} {option.stay.nightly_price.currency}/晚
              </span>{' '}
              · 总计 <span className="ts-mono">{Math.round(option.stay.total_price.amount)} {option.stay.total_price.currency}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs">
        <div className="rounded-full px-3 py-1 text-zinc-200" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}>
          旅行时间 <span className="ts-mono">{option.scorecard.total_travel_time_hours.toFixed(1)}</span> 小时
        </div>
        <div className="rounded-full px-3 py-1 text-zinc-200" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}>
          转机 {option.scorecard.num_transfers} 次
        </div>
        <div className="rounded-full px-3 py-1 text-zinc-200" style={{ border: '1px solid var(--ts-border)', background: 'rgba(2,6,23,0.35)' }}>
          日通勤估计 <span className="ts-mono">{option.metrics.daily_commute_minutes_estimate}</span> 分钟
        </div>
      </div>

      {option.warnings?.length ? (
        <div className="mt-4 rounded-2xl px-3 py-2 text-xs text-amber-200" style={{ border: '1px solid rgba(245,158,11,0.35)', background: 'rgba(120,53,15,0.18)' }}>
          {option.warnings.join('；')}
        </div>
      ) : null}

      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <button
          className="ts-btn-primary flex-1"
          onClick={onGenerate}
          type="button"
          aria-label="生成详细行程"
        >
          生成详细行程
        </button>
        {onSave ? (
          <button
            className="ts-btn-secondary flex-1"
            onClick={onSave}
            type="button"
            aria-label="保存此方案"
          >
            保存此方案
          </button>
        ) : null}
        <button
          className="ts-btn-secondary flex-1"
          onClick={onAlert}
          type="button"
          aria-label="订阅价格提醒"
        >
          订阅价格提醒
        </button>
      </div>
    </div>
  )
}

