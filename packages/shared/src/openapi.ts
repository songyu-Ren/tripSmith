export type ErrorResponse = {
  error: {
    code: string
    message: string
    details?: Record<string, unknown> | null
  }
}

export type TripCreateRequest = {
  origin: string
  destination: string
  start_date: string
  end_date: string
  flexible_days?: number
  budget_total: number
  currency?: string
  travelers?: number
  preferences?: Record<string, unknown>
}

export type TripDto = {
  id: string
  user_id: string
  created_at: string
  origin: string
  destination: string
  start_date: string
  end_date: string
  flexible_days: number
  budget_total: number
  currency: string
  travelers: number
  preferences: Record<string, unknown>
}

export type Money = { amount: number; currency: string }

export type FlightSummary = {
  depart_at: string
  arrive_at: string
  stops: number
  duration_minutes: number
  price: Money
}

export type StaySummary = {
  name: string
  area: string
  nightly_price: Money
  total_price: Money
}

export type PlanScores = {
  cost_score: number
  time_score: number
  comfort_score: number
}

export type PlanMetrics = {
  total_price: Money
  total_flight_minutes: number
  transfer_count: number
  daily_commute_minutes_estimate: number
}

export type PlanOption = {
  label: 'cheap' | 'fast' | 'balanced'
  title: string
  flight: FlightSummary
  stay: StaySummary
  metrics: PlanMetrics
  scores: PlanScores
  explanation: string
  warnings: string[]
}

export type PlansJson = {
  generated_at: string
  options: PlanOption[]
}

export type PlanCreateResponse = {
  plan_id: string
  plans_json: PlansJson
  explain_md: string
}

export type TripGetResponse = {
  trip: TripDto
  latest_plan_id: string | null
  latest_plans_json: PlansJson | null
  latest_explain_md: string | null
}

export type ItineraryCreateRequest = { plan_index: number }

export type Commute = { mode: 'walk' | 'drive' | 'transit' | 'estimate'; minutes: number }

export type ItineraryItem = {
  period: 'morning' | 'afternoon' | 'evening'
  poi_name: string
  stay_minutes: number
  commute: Commute
  weather_summary: string
}

export type ItineraryDay = { date: string; items: ItineraryItem[] }

export type ItineraryJson = {
  generated_at: string
  plan_index: number
  days: ItineraryDay[]
}

export type ItineraryCreateResponse = {
  itinerary_id: string
  itinerary_json: ItineraryJson
  itinerary_md: string
}

export type AlertCreateRequest = {
  trip_id: string
  type: 'flight' | 'hotel' | 'both'
  threshold: number
  frequency_minutes: number
}

export type AlertDto = {
  id: string
  trip_id: string
  type: string
  threshold: number
  frequency_minutes: number
  last_checked_at: string | null
  is_active: boolean
}

export type AlertCreateResponse = { alert: AlertDto }

