// src/services/adminApi.js
import axios from "axios";
import { auth } from "../stores/auth";
import { normalizeApiError } from "./api";

const base = import.meta.env.VITE_ADMIN_BASE_URL || import.meta.env.VITE_ADMIN_URL;
const normalizedBase = String(base).replace(/\/$/, "");

export const adminApi = axios.create({
  baseURL: normalizedBase,
  timeout: 20000
});

adminApi.interceptors.request.use((config) => {
  const token = auth.token();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export { normalizeApiError };

// Helpers (API)
export async function getOverview() {
  return adminApi.get("/admin/overview");
}

export async function listAreas() {
  return adminApi.get("/admin/catalog/areas");
}

export async function createArea(name) {
  return adminApi.post("/admin/catalog/areas", { name });
}

export async function patchArea(id, payload) {
  return adminApi.patch(`/admin/catalog/areas/${id}`, payload);
}

export async function listFlags() {
  return adminApi.get("/admin/flags");
}

export async function setFlag(key, enabled) {
  return adminApi.put(`/admin/flags/${key}`, { enabled });
}


// Catálogo (lectura para profesionales/admin)
export async function listPublicAreas() {
  try {
    const { data } = await adminApi.get('/catalog/areas');
    return data;
  } catch (e) {
    throw normalizeApiError(e);
  }
}
