'use client'

import { useEffect, useRef, useState } from 'react'
import type { JobDto } from '@tripsmith/shared'

import { api } from '@/lib/api'

type Options = {
  enabled?: boolean
  intervalMs?: number
  onSucceeded?: (job: JobDto) => void | Promise<void>
  onFailed?: (job: JobDto) => void | Promise<void>
}

export function useJobPoll(jobId: string | null, opts: Options = {}) {
  const { enabled = true, intervalMs = 1000, onSucceeded, onFailed } = opts
  const [job, setJob] = useState<JobDto | null>(null)
  const [error, setError] = useState<unknown | null>(null)
  const callbacksRef = useRef({ onSucceeded, onFailed })
  callbacksRef.current = { onSucceeded, onFailed }

  useEffect(() => {
    if (!enabled || !jobId) return
    let stopped = false
    const currentJobId = jobId

    async function tick() {
      try {
        const j = await api().getJob(currentJobId)
        if (stopped) return
        setJob(j)
        setError(null)

        if (j.status === 'succeeded') {
          stopped = true
          await callbacksRef.current.onSucceeded?.(j)
        } else if (j.status === 'failed') {
          stopped = true
          await callbacksRef.current.onFailed?.(j)
        }
      } catch (e) {
        if (!stopped) setError(e)
      }
    }

    const id = setInterval(() => void tick(), intervalMs)
    void tick()
    return () => {
      stopped = true
      clearInterval(id)
    }
  }, [enabled, intervalMs, jobId])

  return { job, error }
}
