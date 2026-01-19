// src/services/claimsApi.js
import axios from 'axios'
import { auth } from '../stores/auth'
import { normalizeApiError } from './api'

function normalizeListResponse(data){
  if(Array.isArray(data)) return data
  if(data && Array.isArray(data.items)) return data.items
  return []
}

const base = import.meta.env.VITE_CLAIMS_BASE_URL || import.meta.env.VITE_CLAIMS_URL
const normalizedBase = String(base).replace(/\/$/, '')

const http = axios.create({
  baseURL: normalizedBase,
  timeout: 10000
})

http.interceptors.request.use((config) => {
  const token = auth.token()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function health() {
  try {
    const { data } = await http.get('/health')
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function listClaims(params = {}) {
  try {
    const { data } = await http.get('/claims', { params })
    return normalizeListResponse(data)
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function getClaim(id) {
  try {
    const { data } = await http.get(`/claims/${id}`)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function createClaim(payload) {
  try {
    const { data } = await http.post('/claims', payload)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function patchClaim(id, payload) {
  try {
    const { data } = await http.patch(`/claims/${id}`, payload)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function submitClaim(id) {
  try {
    const { data } = await http.post(`/claims/${id}/submit`)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function reviewClaim(id, payload) {
  try {
    const { data } = await http.post(`/claims/${id}/review`, payload)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function payClaim(id, payload) {
  try {
    const { data } = await http.post(`/claims/${id}/payment`, payload)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function getTimeline(id) {
  try {
    const { data } = await http.get(`/claims/${id}/timeline`)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function getDocuments(id) {
  try {
    const { data } = await http.get(`/claims/${id}/documents`)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function addDocument(id, payload) {
  try {
    const { data } = await http.post(`/claims/${id}/documents`, payload)
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}

export async function getOverview() {
  try {
    const { data } = await http.get('/claims/overview')
    return data
  } catch (e) {
    throw new Error(normalizeApiError(e))
  }
}
