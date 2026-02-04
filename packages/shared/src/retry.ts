export type RetryOptions = {
  retries: number
  baseDelayMs: number
  getDelayMs?: (err: unknown, attemptIndex: number) => number | undefined
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  opts: RetryOptions
): Promise<T> {
  let lastErr: unknown
  for (let i = 0; i <= opts.retries; i += 1) {
    try {
      return await fn()
    } catch (err) {
      lastErr = err
      if (i === opts.retries) break
      const customDelay = opts.getDelayMs?.(err, i)
      const delay = customDelay ?? opts.baseDelayMs * Math.pow(2, i)
      await new Promise((r) => setTimeout(r, delay))
    }
  }
  throw lastErr
}

