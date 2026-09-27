export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export function requestHeaders(token?: string) {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'X-Request-ID': crypto.randomUUID(),
    'X-Correlation-ID': crypto.randomUUID(),
  }
  if (token?.trim()) headers.Authorization = token.trim()
  return headers
}

export async function apiFetch<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...requestHeaders(token),
      ...(options.headers || {}),
    },
  })
  const raw = await res.text()
  let body: unknown = null
  try { body = raw ? JSON.parse(raw) : null } catch { body = raw }
  if (!res.ok) {
    const message = typeof body === 'object' && body && 'detail' in body ? String((body as {detail: unknown}).detail) : `HTTP ${res.status}`
    throw new Error(message)
  }
  return body as T
}
