// src/services/reportsApi.js
import axios from 'axios'
import { auth } from '../stores/auth'
import { normalizeApiError } from './api'

const base = import.meta.env.VITE_REPORTS_BASE_URL || import.meta.env.VITE_REPORTS_URL
const normalizedBase = String(base).replace(/\/$/, '')

export const reportsApi = axios.create({
  baseURL: normalizedBase,
  timeout: 20000
})

reportsApi.interceptors.request.use((config) => {
  const token = auth.token()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function getReportsSummary(window = '7d') {
  return getSummary(window)
}

export async function getSummary(window = '7d') {
  try {
    const { data } = await reportsApi.get('/reports/summary', { params: { window } })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function getActivity(params) {
  try {
    const { data } = await reportsApi.get('/reports/activity', { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function getCases(params) {
  try {
    const { data } = await reportsApi.get('/reports/cases', { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function getAppointments(params) {
  try {
    const { data } = await reportsApi.get('/reports/appointments', { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function getSecurity(params) {
  try {
    const { data } = await reportsApi.get('/reports/security', { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function getTopActors(params) {
  try {
    const { data } = await reportsApi.get('/reports/top-actors', { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function getMine(params) {
  try {
    const { data } = await reportsApi.get('/reports/mine', { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function createExport(payload) {
  try {
    const { data } = await reportsApi.post('/reports/export', payload)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function getExportStatus(job_id) {
  try {
    const { data } = await reportsApi.get(`/reports/export/${encodeURIComponent(job_id)}`)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export function exportDownloadUrl(job_id) {
  return `${normalizedBase}/reports/export/${encodeURIComponent(job_id)}/download`
}
