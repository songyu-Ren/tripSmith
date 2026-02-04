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
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{option.title}</div>
          <div className="mt-1 text-xs text-zinc-400">{option.explanation}</div>
        </div>
        <div className="text-right">
          <div className="text-sm font-semibold">
            {Math.round(option.scorecard.total_cost)} {option.scorecard.currency}
          </div>
          <div className="text-xs text-zinc-400">总价</div>
        </div>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-5">
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/30 px-3 py-2 text-xs text-zinc-300">
          费用 {Math.round(option.scorecard.cost_score)}/100
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/30 px-3 py-2 text-xs text-zinc-300">
          时间 {Math.round(option.scorecard.time_score)}/100
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/30 px-3 py-2 text-xs text-zinc-300">
          舒适 {Math.round(option.scorecard.comfort_score)}/100
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/30 px-3 py-2 text-xs text-zinc-300">
          通勤 {Math.round(option.scorecard.commute_score)}/100
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/30 px-3 py-2 text-xs text-zinc-300">
          日负荷 {Math.round(option.scorecard.daily_load_score)}/100
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/30 p-3">
          <div className="text-xs font-medium text-zinc-200">航班摘要</div>
          <div className="mt-2 space-y-1 text-xs text-zinc-300">
            <div>
              {option.flight.depart_at} → {option.flight.arrive_at}
            </div>
            <div>
              转机 {option.flight.stops} 次 · {option.flight.duration_minutes} 分钟 ·{' '}
              {Math.round(option.flight.price.amount)} {option.flight.price.currency}
            </div>
          </div>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/30 p-3">
          <div className="text-xs font-medium text-zinc-200">住宿摘要</div>
          <div className="mt-2 space-y-1 text-xs text-zinc-300">
            <div>{option.stay.name}</div>
            <div>
              {option.stay.area} · {Math.round(option.stay.nightly_price.amount)}{' '}
              {option.stay.nightly_price.currency}/晚 · 总计 {Math.round(option.stay.total_price.amount)}{' '}
              {option.stay.total_price.currency}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs">
        <div className="rounded-full border border-zinc-800 bg-zinc-950/30 px-3 py-1 text-zinc-300">
          旅行时间 {option.scorecard.total_travel_time_hours.toFixed(1)} 小时
        </div>
        <div className="rounded-full border border-zinc-800 bg-zinc-950/30 px-3 py-1 text-zinc-300">
          转机 {option.scorecard.num_transfers} 次
        </div>
        <div className="rounded-full border border-zinc-800 bg-zinc-950/30 px-3 py-1 text-zinc-300">
          日通勤估计 {option.metrics.daily_commute_minutes_estimate} 分钟
        </div>
      </div>

      {option.warnings?.length ? (
        <div className="mt-4 rounded-lg border border-amber-900/50 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">
          {option.warnings.join('；')}
        </div>
      ) : null}

      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <button
          className="flex-1 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium hover:bg-indigo-500"
          onClick={onGenerate}
          type="button"
        >
          生成详细行程
        </button>
        {onSave ? (
          <button
            className="flex-1 rounded-lg border border-zinc-700 bg-zinc-950/30 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800"
            onClick={onSave}
            type="button"
          >
            保存此方案
          </button>
        ) : null}
        <button
          className="flex-1 rounded-lg border border-zinc-700 bg-zinc-950/30 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800"
          onClick={onAlert}
          type="button"
        >
          订阅价格提醒
        </button>
      </div>
    </div>
  )
}

