// src/services/coverageApi.js
import axios from 'axios'
import { auth } from '../stores/auth'
import { normalizeApiError } from './api'

function normalizeListResponse(data){
  if(Array.isArray(data)) return data
  if(data && Array.isArray(data.items)) return data.items
  return []
}

const base = import.meta.env.VITE_COVERAGE_BASE_URL || import.meta.env.VITE_COVERAGE_URL || 'http://localhost:8010'
const normalizedBase = String(base).replace(/\/$/, '')

const http = axios.create({
  baseURL: normalizedBase,
  timeout: 12000
})

http.interceptors.request.use((config) => {
  const token = auth.token()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function listCoverages() {
  try {
    const { data } = await http.get('/coverage')
    return normalizeListResponse(data)
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function getCoverage(id) {
  try {
    const { data } = await http.get(`/coverage/${encodeURIComponent(id)}`)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function listCoverageByClaimType(claim_type) {
  try {
    const { data } = await http.get(`/coverage/by-claim-type/${encodeURIComponent(claim_type)}`)
    return normalizeListResponse(data)
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

// Admin only
export async function createCoverage(payload) {
  try {
    const { data } = await http.post('/coverage', payload)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function patchCoverage(id, payload) {
  try {
    const { data } = await http.patch(`/coverage/${encodeURIComponent(id)}`, payload)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function activateCoverage(id) {
  try {
    const { data } = await http.post(`/coverage/${encodeURIComponent(id)}/activate`)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function deactivateCoverage(id) {
  try {
    const { data } = await http.post(`/coverage/${encodeURIComponent(id)}/deactivate`)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}
