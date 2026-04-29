export function getToken() {
  try {
    return sessionStorage.getItem('cubatron_token') || null
  } catch (e) {
    return null
  }
}

export async function apiFetch(path, options = {}) {
  const headers = Object.assign({}, options.headers || {})
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (!headers['Accept']) headers['Accept'] = 'application/json'
  options.headers = headers

  const res = await fetch(path, options)
  if (res.status === 401) throw new Error('unauthorized')
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = data.detail || data.error || data.message || 'API error'
    const e = new Error(err)
    e.status = res.status
    throw e
  }
  return data
}
