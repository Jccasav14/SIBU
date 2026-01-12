// src/services/usersApi.js
import axios from 'axios'
import { auth } from '../stores/auth'
import { normalizeApiError } from './api'

const base = import.meta.env.VITE_USERS_BASE_URL || import.meta.env.VITE_USERS_BASE || import.meta.env.VITE_USERS_URL || 'http://localhost:8001'
const normalizedBase = String(base).replace(/\/$/, '')

// OJO: aquí NO le sumes /auth. Users normalmente va en /users/...
export const usersApi = axios.create({
  baseURL: normalizedBase, // ejemplo: http://localhost:8001
  timeout: 15000
})

usersApi.interceptors.request.use((config) => {
  const token = auth.token()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// helpers
export async function getMe() {
  try {
    const { data } = await usersApi.get('/users/me')
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function updateMe(payload) {
  try {
    const { data } = await usersApi.put('/users/me', payload)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

// ADMIN
export async function adminCreateUser(payload) {
  try {
    const { data } = await usersApi.post('/users', payload)
    return data // { email, temp_password }
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function adminGetUserByEmail(email) {
  try {
    const { data } = await usersApi.get(`/users/${encodeURIComponent(email)}`)
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}

export async function adminSetActive(email, active) {
  try {
    const { data } = await usersApi.patch(
      `/users/${encodeURIComponent(email)}/active`,
      null,
      { params: { active } }
    )
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}


export async function listUsers(params = {}) {
  try {
    const { data } = await usersApi.get('/users', { params })
    return data
  } catch (err) {
    throw new Error(normalizeApiError(err))
  }
}
