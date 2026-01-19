// src/services/appointmentsApi.js
import axios from 'axios'
import { auth } from '../stores/auth'
import { normalizeApiError } from './api'

const base = import.meta.env.VITE_APPOINTMENTS_BASE_URL || import.meta.env.VITE_APPOINTMENTS_URL
const normalizedBase = String(base).replace(/\/$/, '')

export const appointmentsApi = axios.create({
  baseURL: normalizedBase,
  timeout: 20000
})

appointmentsApi.interceptors.request.use((config) => {
  const token = auth.token()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function listAvailability(params = {}) {
  try {
    const { data } = await appointmentsApi.get('/availability', { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function createAvailability(payload) {
  try {
    const { data } = await appointmentsApi.post('/availability', payload)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function createAppointment(payload) {
  try {
    const { data } = await appointmentsApi.post('/appointments', payload)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function listAppointmentsMine(params = {}) {
  try {
    const { data } = await appointmentsApi.get('/appointments/mine', { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function patchAppointmentStatus(id, status) {
  try {
    const { data } = await appointmentsApi.patch(`/appointments/${encodeURIComponent(id)}/status`, { status })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}


export async function updateAvailability(id, payload) {
  try {
    const { data } = await appointmentsApi.patch(`/availability/${id}`, payload)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function deleteAvailability(id) {
  try {
    await appointmentsApi.delete(`/availability/${id}`)
    return true
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}
