<template>
  <section class="card">
    <h2>Perfil (GET /auth/me)</h2>

    <p v-if="loading"><small class="muted">Cargando...</small></p>
    <p v-if="error" class="err">{{ error }}</p>

    <div v-if="me">
      <p><b>Email:</b> {{ me.email }}</p>
      <p><b>Role:</b> {{ me.role }}</p>
      <hr />
      <p><small class="muted">Token guardado en localStorage (solo para este microservicio).</small></p>
    </div>

    <div style="margin-top:12px">
      <button class="primary" @click="load" :disabled="loading">Actualizar</button>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api, normalizeApiError } from '../services/api'

const me = ref(null)
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/me')
    me.value = data
  } catch (e) {
    error.value = normalizeApiError(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
