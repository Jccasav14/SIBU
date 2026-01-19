import axios from 'axios'
import { auth } from '../stores/auth'

// WEB: VITE_AUTH_BASE_URL | MOBILE: VITE_AUTH_URL
const base = import.meta.env.VITE_AUTH_BASE_URL || import.meta.env.VITE_AUTH_URL || import.meta.env.VITE_AUTH_URL
const normalizedBase = String(base).replace(/\/$/, '')

export const api = axios.create({
  baseURL: normalizedBase + '/auth',
  timeout: 15000
})

api.interceptors.request.use((config) => {
  const token = auth.token()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/* ✅ EXPORT CORRECTO */
export function normalizeApiError(err) {
  const data = err?.response?.data
  if (!data) return 'Error de red. Revisa que el auth esté levantado.'

  if (typeof data === 'string') return data
  if (data.detail) {
    if (typeof data.detail === 'string') return data.detail
    return JSON.stringify(data.detail)
  }

  return JSON.stringify(data)
}
