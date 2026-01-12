<template>
  <section class="card">
    <header class="head">
      <h2>Cambiar contraseña</h2>
      <p class="muted">Debes actualizar tu contraseña para continuar</p>
    </header>

    <form @submit.prevent="onSubmit">
      <div class="row">
        <label>Contraseña actual</label>
        <input v-model="current" type="password" required />
      </div>

      <div class="row">
        <label>Nueva contraseña</label>
        <input v-model="next" type="password" minlength="8" required />
      </div>

      <p v-if="error" class="err">{{ error }}</p>
      <p v-if="ok" class="ok">{{ ok }}</p>

      <button class="primary" type="submit" :disabled="loading">
        {{ loading ? 'Guardando...' : 'Actualizar contraseña' }}
      </button>
    </form>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, normalizeApiError } from '../services/api'
import { auth } from '../stores/auth'

const router = useRouter()

const current = ref('')
const next = ref('')
const loading = ref(false)
const error = ref('')
const ok = ref('')

async function onSubmit() {
  loading.value = true
  error.value = ''
  ok.value = ''

  try {
    await api.post('/change-password', {
      current_password: current.value,
      new_password: next.value
    })

    // ✅ actualiza el store EN MEMORIA + localStorage
    auth.updateUser({ must_change_password: false })

    ok.value = 'Contraseña actualizada ✅'

    current.value = ''
    next.value = ''

    // ✅ redirige por rol (no hardcode)
    const role = auth.user()?.role
    if (role === 'professional') router.replace('/dashboard')
    else if (role === 'admin') router.replace('/admin')
    else router.replace('/me')

  } catch (e) {
    error.value = normalizeApiError(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.card {
  max-width: 520px;
  margin: 0 auto;
  padding: 24px;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  box-shadow: 0 6px 20px rgba(0,0,0,0.05);
}

.head { margin-bottom: 20px; }
.head h2 { margin: 0 0 6px; font-size: 1.5rem; }

.muted { color: #6b7280; font-size: 0.85rem; }

.row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}

label { font-size: 0.85rem; font-weight: 500; color: #374151; }

input {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  font-size: 0.9rem;
}

input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}

button.primary {
  width: 100%;
  margin-top: 10px;
  padding: 10px;
  border-radius: 10px;
  border: none;
  background: #2563eb;
  color: white;
  font-size: 0.95rem;
  cursor: pointer;
}

button.primary:disabled { opacity: 0.7; cursor: not-allowed; }

.err {
  color: #b91c1c;
  background: #fef2f2;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #fecaca;
  margin-bottom: 10px;
}

.ok {
  color: #065f46;
  background: #ecfdf5;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #a7f3d0;
  margin-bottom: 10px;
}
</style>
