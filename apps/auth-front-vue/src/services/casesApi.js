// src/services/casesApi.js
import axios from 'axios'
import { auth } from '../stores/auth'
import { normalizeApiError } from './api'

const base = import.meta.env.VITE_CASES_BASE_URL || import.meta.env.VITE_CASES_URL || 'http://localhost:8003'
const normalizedBase = String(base).replace(/\/$/, '')

export const casesApi = axios.create({
  baseURL: normalizedBase, // ejemplo: http://localhost:8003
  timeout: 15000
})

casesApi.interceptors.request.use((config) => {
  const token = auth.token()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// --------- helpers (MVP) ---------
export async function createCase(payload) {
  try {
    const { data } = await casesApi.post('/cases', payload)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function listCases(params = {}) {
  try {
    const { data } = await casesApi.get('/cases', { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function listCasesByStudent(studentId, params = {}) {
  try {
    const { data } = await casesApi.get(`/cases/by-student/${encodeURIComponent(studentId)}`, { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function getCase(caseId) {
  try {
    const { data } = await casesApi.get(`/cases/${encodeURIComponent(caseId)}`)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function updateCase(caseId, payload) {
  try {
    const { data } = await casesApi.patch(`/cases/${encodeURIComponent(caseId)}`, payload)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function assignCase(caseId, professionalId) {
  try {
    const { data } = await casesApi.post(`/cases/${encodeURIComponent(caseId)}/assign`, {
      professional_id: professionalId
    })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function changeCaseStatus(caseId, status) {
  try {
    const { data } = await casesApi.post(`/cases/${encodeURIComponent(caseId)}/status`, { status })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function shareCase(caseId, payload) {
  try {
    const { data } = await casesApi.post(`/cases/${encodeURIComponent(caseId)}/share`, payload)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function addCaseNote(caseId, payload) {
  try {
    const { data } = await casesApi.post(`/cases/${encodeURIComponent(caseId)}/notes`, payload)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function listCaseNotes(caseId, params = {}) {
  try {
    const { data } = await casesApi.get(`/cases/${encodeURIComponent(caseId)}/notes`, { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function getCaseTimeline(caseId, params = {}) {
  try {
    const { data } = await casesApi.get(`/cases/${encodeURIComponent(caseId)}/timeline`, { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}
