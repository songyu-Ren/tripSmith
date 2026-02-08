'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { TripCreateRequest } from '@tripsmith/shared'

import { api } from '@/lib/api'
import { ErrorPanel } from '@/components/ErrorPanel'
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
  const [error, setError] = useState<unknown | null>(null)

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
      setError(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="space-y-2">
        <h1 className="text-lg font-semibold">Start planning your trip</h1>
        <p className="text-sm ts-muted">
          Enter your preferences to generate 3 options (budget/time/balanced), then export or subscribe to price alerts.
        </p>
      </div>

      <div className="ts-card">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Origin (origin)">
            <input
              className="ts-input"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
            />
          </Field>
          <Field label="Destination (destination)">
            <input
              className="ts-input"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
            />
          </Field>
          <Field label="Start date">
            <input
              type="date"
              className="ts-input"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </Field>
          <Field label="End date">
            <input
              type="date"
              className="ts-input"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </Field>
          <Field label="Flex days (± days)">
            <input
              className="ts-input"
              value={flexDays}
              onChange={(e) => setFlexDays(e.target.value)}
              inputMode="numeric"
            />
          </Field>
          <Field label="Total budget (USD)">
            <input
              className="ts-input"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              inputMode="decimal"
            />
          </Field>
          <Field label="Travelers">
            <input
              className="ts-input"
              value={travelers}
              onChange={(e) => setTravelers(e.target.value)}
              inputMode="numeric"
            />
          </Field>
          <Field label="Preferences (comma-separated)" hint="Example: balanced,walkable,food">
            <input
              className="ts-input"
              value={prefs}
              onChange={(e) => setPrefs(e.target.value)}
            />
          </Field>
        </div>

        {error ? (
          <div className="mt-4">
            <ErrorPanel error={error} onRetry={submit} />
          </div>
        ) : null}

        <button
          className="ts-btn-primary mt-4 w-full"
          onClick={submit}
          disabled={!valid || loading}
          type="button"
        >
          {loading ? 'Creating…' : 'Generate plans'}
        </button>
      </div>

      <div className="ts-card text-sm">
        <div className="font-medium">Notes</div>
        <ul className="mt-2 list-disc space-y-1 pl-5 ts-muted">
          <li>Mock providers are enabled by default, so it works end-to-end without any keys.</li>
          <li>Real POI/weather/routing providers can be enabled via `.env`.</li>
        </ul>
      </div>
    </div>
  )
}

