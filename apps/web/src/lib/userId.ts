const COOKIE = 'tripsmith_uid'

function getCookieValue(name: string): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

function setCookieValue(name: string, value: string): void {
  if (typeof document === 'undefined') return
  const maxAge = 60 * 60 * 24 * 365
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAge}; SameSite=Lax`
}

export function getOrCreateUserId(): string {
  const existing = getCookieValue(COOKIE)
  if (existing) return existing
  const uid = globalThis.crypto?.randomUUID
    ? globalThis.crypto.randomUUID()
    : `uid_${Math.random().toString(16).slice(2)}_${Date.now()}`
  setCookieValue(COOKIE, uid)
  return uid
}

