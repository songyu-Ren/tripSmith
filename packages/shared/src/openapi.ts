export type ErrorResponse = {
  error_code: string
  message: string
  request_id: string
  details?: unknown
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
  constraints?: Constraints | null
  constraints_confirmed_at?: string | null
  constraints_confirmed?: boolean
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
  daily_load_score: number
  commute_score: number
  cost_score: number
  time_score: number
  comfort_score: number
}

export type PlanScorecard = {
  total_cost: number
  currency: string
  total_travel_time_hours: number
  num_transfers: number
  daily_load_score: number
  commute_score: number
  comfort_score: number
  cost_score: number
  time_score: number
  rationale_md: string
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
  scorecard: PlanScorecard
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

export type JobDto = {
  id: string
  trip_id: string
  type: 'plan' | 'itinerary'
  status: 'queued' | 'running' | 'succeeded' | 'failed'
  stage: string
  progress: number
  message: string
  result_json: Record<string, unknown> | null
  error_code?: string | null
  error_message?: string | null
  next_action?: string | null
  created_at: string
  updated_at: string
}

export type JobCreateResponse = { job_id: string }

export type SavedPlanDto = {
  id: string
  trip_id: string
  plan_id: string
  plan_index: number
  created_at: string
  label: string
}

export type SavePlanRequest = { plan_id: string; plan_index: number; label: string }

export type SavePlanResponse = { saved_plan: SavedPlanDto }

export type SavedPlansListResponse = { saved_plans: SavedPlanDto[] }

export type Constraints = {
  pace: 'relaxed' | 'balanced' | 'packed'
  walking_tolerance_km_per_day: number
  max_daily_activity_hours?: number
  max_daily_commute_hours?: number
  max_transfer_count: number
  hotel_star_min?: number | null
  night_flight_allowed: boolean
}

export type ConstraintsGenerateResponse = { constraints: Constraints }

export type ConstraintsUpdateRequest = { constraints: Constraints }

export type ConstraintsGetResponse = {
  constraints: Constraints | null
  confirmed: boolean
}

export type ItineraryCreateRequest = { plan_index: number; plan_id?: string | null }

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

