import {
  AlertCreateRequest,
  AlertCreateResponse,
  ItineraryCreateRequest,
  ItineraryCreateResponse,
  PlanCreateResponse,
  TripCreateRequest,
  TripDto,
  TripGetResponse,
  ErrorResponse
} from './openapi'
import { withRetry } from './retry'

export type ApiClientOptions = {
  baseUrl: string
  userId: string
}

export type ApiError = {
  status: number
  data?: ErrorResponse
  message: string
}

async function parseError(resp: Response): Promise<ErrorResponse | undefined> {
  const ct = resp.headers.get('content-type') || ''
  if (!ct.includes('application/json')) return undefined
  try {
    return (await resp.json()) as ErrorResponse
  } catch {
    return undefined
  }
}

async function requestJson<T>(
  opts: ApiClientOptions,
  path: string,
  init: RequestInit
): Promise<T> {
  const url = opts.baseUrl.replace(/\/$/, '') + path
  const resp = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': opts.userId,
      ...(init.headers || {})
    }
  })

  if (resp.ok) {
    return (await resp.json()) as T
  }

  const data = await parseError(resp)
  const err: ApiError = {
    status: resp.status,
    data,
    message: data?.error?.message || `HTTP ${resp.status}`
  }
  throw err
}

export function createApiClient(opts: ApiClientOptions) {
  const retry = { retries: 2, baseDelayMs: 250 }

  return {
    createTrip: (payload: TripCreateRequest) =>
      withRetry(() => requestJson<TripDto>(opts, '/api/trips', {
        method: 'POST',
        body: JSON.stringify(payload)
      }), retry),

    getTrip: (tripId: string) =>
      withRetry(() => requestJson<TripGetResponse>(opts, `/api/trips/${tripId}`, {
        method: 'GET'
      }), retry),

    createPlan: (tripId: string) =>
      withRetry(() => requestJson<PlanCreateResponse>(opts, `/api/trips/${tripId}/plan`, {
        method: 'POST'
      }), retry),

    createItinerary: (tripId: string, payload: ItineraryCreateRequest) =>
      withRetry(() => requestJson<ItineraryCreateResponse>(opts, `/api/trips/${tripId}/itinerary`, {
        method: 'POST',
        body: JSON.stringify(payload)
      }), retry),

    createAlert: (payload: AlertCreateRequest) =>
      withRetry(() => requestJson<AlertCreateResponse>(opts, '/api/alerts', {
        method: 'POST',
        body: JSON.stringify(payload)
      }), retry)
  }
}

