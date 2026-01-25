'use client'

import { createApiClient } from '@tripsmith/shared'
import { getApiBaseUrl } from '@/lib/env'
import { getOrCreateUserId } from '@/lib/userId'

export function api() {
  return createApiClient({ baseUrl: getApiBaseUrl(), userId: getOrCreateUserId() })
}

