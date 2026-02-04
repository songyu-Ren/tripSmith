import {
  AlertCreateRequest,
  AlertCreateResponse,
  ConstraintsGenerateResponse,
  ConstraintsGetResponse,
  ConstraintsUpdateRequest,
  ItineraryCreateRequest,
  JobCreateResponse,
  JobDto,
  SavePlanRequest,
  SavePlanResponse,
  SavedPlansListResponse,
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

export class ApiError extends Error {
  status: number
  data?: ErrorResponse
  errorCode?: string
  requestId?: string
  retryAfterSeconds?: number

  constructor(init: {
    status: number
    message: string
    data?: ErrorResponse
    retryAfterSeconds?: number
  }) {
    super(init.message)
    this.name = 'ApiError'
    this.status = init.status
    this.data = init.data
    this.errorCode = init.data?.error_code
    this.requestId = init.data?.request_id
    this.retryAfterSeconds = init.retryAfterSeconds
  }
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
  const retryAfterHeader = resp.headers.get('retry-after')
  const retryAfterSeconds =
    retryAfterHeader && /^\d+$/.test(retryAfterHeader)
      ? parseInt(retryAfterHeader, 10)
      : undefined

  throw new ApiError({
    status: resp.status,
    data,
    retryAfterSeconds,
    message: data?.message || `HTTP ${resp.status}`
  })
}

export function createApiClient(opts: ApiClientOptions) {
  const retry = {
    retries: 2,
    baseDelayMs: 250,
    getDelayMs: (err: unknown, attemptIndex: number) => {
      if (err instanceof ApiError && err.retryAfterSeconds) {
        return err.retryAfterSeconds * 1000
      }
      return 250 * Math.pow(2, attemptIndex)
    }
  }

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

    getConstraints: (tripId: string) =>
      withRetry(() => requestJson<ConstraintsGetResponse>(opts, `/api/trips/${tripId}/constraints`, {
        method: 'GET'
      }), retry),

    generateConstraints: (tripId: string) =>
      withRetry(() => requestJson<ConstraintsGenerateResponse>(opts, `/api/trips/${tripId}/constraints/generate`, {
        method: 'POST'
      }), retry),

    confirmConstraints: (tripId: string, payload: ConstraintsUpdateRequest) =>
      withRetry(() => requestJson<ConstraintsGetResponse>(opts, `/api/trips/${tripId}/constraints`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      }), retry),

    getJob: (jobId: string) =>
      withRetry(() => requestJson<JobDto>(opts, `/api/jobs/${jobId}`, {
        method: 'GET'
      }), retry),

    createPlan: (tripId: string) =>
      withRetry(() => requestJson<JobCreateResponse>(opts, `/api/trips/${tripId}/plan`, {
        method: 'POST'
      }), retry),

    createItinerary: (tripId: string, payload: ItineraryCreateRequest) =>
      withRetry(() => requestJson<JobCreateResponse>(opts, `/api/trips/${tripId}/itinerary`, {
        method: 'POST',
        body: JSON.stringify(payload)
      }), retry),

    listSavedPlans: (tripId: string) =>
      withRetry(() => requestJson<SavedPlansListResponse>(opts, `/api/trips/${tripId}/saved_plans`, {
        method: 'GET'
      }), retry),

    savePlan: (tripId: string, payload: SavePlanRequest) =>
      withRetry(() => requestJson<SavePlanResponse>(opts, `/api/trips/${tripId}/saved_plans`, {
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

