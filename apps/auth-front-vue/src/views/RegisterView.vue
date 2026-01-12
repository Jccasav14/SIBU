<template>
  <div class="auth-layout">
    <!-- LEFT -->
    <div class="auth-image"></div>

    <!-- RIGHT -->
    <div class="auth-form">
      <h1>Crear cuenta</h1>
      <p>Sistema Integral de Bienestar Universitario</p>

      <form @submit.prevent="onSubmit">
        <input
          v-model.trim="email"
          type="email"
          placeholder="Correo institucional"
          required
        />

        <input
          v-model="password"
          type="password"
          placeholder="Contraseña (mínimo 8 caracteres)"
          minlength="8"
          required
        />

        <select v-model="role" required>
          <option value="insurance">Seguros</option>
          <option value="professional">Profesional</option>
          <option value="admin">Administrador</option>
        </select>

        <p class="muted">
          En producción, los roles <strong>Administrador</strong> y <strong>Seguros</strong> normalmente no deberían
          estar disponibles en el registro público.
        </p>

        <button type="submit" :disabled="loading">
          {{ loading ? "Creando cuenta..." : "Crear cuenta" }}
        </button>

        <p v-if="error" class="auth-error">{{ error }}</p>
        <p v-if="ok" class="auth-ok">{{ ok }}</p>
      </form>

      <p class="switch">
        ¿Ya tienes cuenta?
        <RouterLink to="/login">Inicia sesión</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { api, normalizeApiError } from "../services/api";
import "../styles/auth.css";

const email = ref("");
const password = ref("");
const role = ref("student");
const loading = ref(false);
const error = ref("");
const ok = ref("");

async function onSubmit() {
  error.value = "";
  ok.value = "";
  loading.value = true;

  try {
    const { data } = await api.post("/register", {
      email: email.value,
      password: password.value,
      role: role.value,
    });

    ok.value = data?.msg || "Cuenta creada correctamente. Ahora puedes iniciar sesión.";
  } catch (e) {
    error.value = normalizeApiError(e);
  } finally {
    loading.value = false;
  }
}
</script>
