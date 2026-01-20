<template>
  <div class="auth-layout">
    <!-- LEFT -->
    <div class="auth-image"></div>

    <!-- RIGHT -->
    <div class="auth-form">
      <h1>SIBU</h1>
      <p>Sistema Integral de Bienestar Universitario</p>

      <form @submit.prevent="login">
        <input
          v-model="email"
          type="email"
          placeholder="Correo institucional"
          required
        />

        <input
          v-model="password"
          type="password"
          placeholder="Contraseña"
          required
        />

        <button type="submit" :disabled="loading">
          {{ loading ? "Ingresando..." : "Iniciar sesión" }}
        </button>

        <p v-if="error" class="auth-error">{{ error }}</p>
      </form>

      <a @click="goRegister">Crear cuenta</a>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { auth } from "../stores/auth";
import "../styles/auth.css";

const router = useRouter();

const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

function extractErrorMessage(payload, fallback = "Error al iniciar sesión") {
  if (!payload) return fallback;

  // FastAPI: {detail: "..."} o {detail: {...}} o {detail: [...]}
  if (typeof payload === "string") return payload;
  if (typeof payload.detail === "string") return payload.detail;
  if (payload.detail) return JSON.stringify(payload.detail);

  // cualquier otro objeto
  try {
    return JSON.stringify(payload);
  } catch {
    return fallback;
  }
}

const login = async () => {
  error.value = "";
  loading.value = true;

  try {
    const base = import.meta.env.VITE_AUTH_BASE_URL;

    // 1) LOGIN (JSON) — según tu Swagger
    const res = await fetch(`${base}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
      }),
    });

    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(d, "Credenciales incorrectas"));
    }

    const loginData = await res.json();
    const token = loginData.access_token;

    // 2) /auth/me
    const meRes = await fetch(`${base}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!meRes.ok) {
      const d = await meRes.json().catch(() => ({}));
      throw new Error(extractErrorMessage(d, "No se pudo obtener el usuario"));
    }

    const user = await meRes.json();

    // ✅ normaliza role (ADMIN vs admin)
    if (user?.role) user.role = String(user.role).toLowerCase();

    // ✅ pega el flag que viene del login
    user.must_change_password = Boolean(loginData.must_change_password);

    // 3) Guardar sesión completa
    auth.setSession(token, user);

    // 4) Forzar cambio de contraseña
    if (user.must_change_password) {
      router.push("/change-password");
      return;
    }

    // 5) Redirección por rol
    if (user.role === "admin") router.push("/admin");
    else if (user.role === "professional") router.push("/dashboard");
    else router.push("/me");
  } catch (e) {
    // ✅ nunca [object Object]
    error.value = e?.message ? String(e.message) : "Error al iniciar sesión";
  } finally {
    loading.value = false;
  }
};

const goRegister = () => {
  router.push("/register");
};
</script>
