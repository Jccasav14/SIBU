<template>
  <div class="wrap">
    <!-- PERFIL PROFESIONAL -->
    <section class="card">
      <header class="head">
        <h2>Perfil Profesional</h2>
        <button class="btn" @click="load" :disabled="loading">
          {{ loading ? 'Cargando...' : 'Recargar' }}
        </button>
      </header>

      <p v-if="error" class="err">{{ error }}</p>

      <div v-if="me" class="grid">
        <div class="field">
          <label>Email</label>
          <input :value="me.email" disabled />
        </div>

        <div class="field">
          <label>Rol</label>
          <input :value="authUser?.role || ''" disabled />
        </div>

        <div class="field">
          <label>Área</label>
          <input :value="me.area || ''" disabled />
        </div>

        <div class="field">
          <label>Activo</label>
          <input :value="me.is_active ? 'Sí' : 'No'" disabled />
        </div>

        <hr class="sep" />

        <div class="field">
          <label>Nombre completo</label>
          <input v-model="form.full_name" placeholder="Ej: Juan Pérez" />
        </div>

        <div class="field">
          <label>Teléfono</label>
          <input v-model="form.phone" placeholder="Ej: 09..." />
        </div>

        <div class="field">
          <label>Bio profesional</label>
          <textarea v-model="form.bio" rows="3" placeholder="Especialidad, experiencia..." />
        </div>

        <div class="actions">
          <button class="btn primary" @click="save" :disabled="loading">
            {{ loading ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>

        <p v-if="ok" class="ok">{{ ok }}</p>
        <p v-if="err" class="err">{{ err }}</p>
      </div>

      <p v-else-if="loading" class="muted">Cargando perfil...</p>
      <p v-else class="muted">No se pudo cargar el perfil.</p>
    </section>

    <!-- FUTURO: CASOS / CITAS -->
    <section class="card ghost">
      <h3>Próximamente</h3>
      <p class="muted">
        Aquí aparecerán los <b>casos asignados</b>, <b>agenda de citas</b> y
        <b>notas profesionales</b>.
      </p>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { auth } from '../stores/auth'
import { getMe, updateMe } from '../services/usersApi'

const authUser = auth.user()

const loading = ref(false)
const error = ref('')
const ok = ref('')
const err = ref('')
const me = ref(null)

const form = reactive({
  full_name: '',
  phone: '',
  bio: ''
})

function sync() {
  form.full_name = me.value?.full_name || ''
  form.phone = me.value?.phone || ''
  form.bio = me.value?.bio || ''
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    me.value = await getMe()
    sync()
  } catch (e) {
    error.value = e?.message || 'Error cargando perfil'
  } finally {
    loading.value = false
  }
}

async function save() {
  ok.value = ''
  err.value = ''
  loading.value = true
  try {
    me.value = await updateMe({
      full_name: form.full_name || null,
      phone: form.phone || null,
      bio: form.bio || null
    })
    sync()
    ok.value = 'Perfil actualizado correctamente'
  } catch (e) {
    err.value = e?.message || 'Error guardando perfil'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
/* Layout */
.wrap {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Cards */
.card {
  background: #ffffff;
  border-radius: 14px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.card.ghost {
  background: #f9fafb;
  border-style: dashed;
}

/* Header */
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.head h2 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 600;
}

/* Grid */
.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.sep {
  grid-column: 1 / -1;
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 10px 0;
}

/* Fields */
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 0.85rem;
  font-weight: 500;
  color: #374151;
}

.field input,
.field textarea {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  font-size: 0.9rem;
  transition: border 0.2s, box-shadow 0.2s;
}

.field input:focus,
.field textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}

.field input[disabled] {
  background: #f9fafb;
  color: #6b7280;
}

/* Actions */
.actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

/* Buttons */
.btn {
  padding: 8px 14px;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #f9fafb;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:hover {
  background: #f3f4f6;
}

.btn.primary {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
}

.btn.primary:hover {
  background: #1e40af;
}

/* Messages */
.err {
  color: #b91c1c;
  background: #fef2f2;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #fecaca;
}

.ok {
  color: #065f46;
  background: #ecfdf5;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #a7f3d0;
}

.muted {
  color: #6b7280;
}

/* Responsive */
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .actions {
    justify-content: stretch;
  }

  .btn {
    width: 100%;
  }
}
</style>
