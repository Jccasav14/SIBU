<template>
  <div class="page">
    <header class="head">
      <div class="left">
        <button class="btn" @click="goBack">← Volver</button>
        <div>
          <h1>Nuevo caso</h1>
          <p class="muted">Crea un caso vinculado a un estudiante. Luego podrás asignar, compartir y registrar notas.</p>
        </div>
      </div>
    </header>

    <section class="card">
      <form class="formGrid" @submit.prevent="onCreate">
        <div class="field">
          <label>ID del estudiante</label>
          <input v-model.trim="create.student_id" required placeholder="Ej: 2024-00123 / CI / código interno" />
        </div>

        <div class="field">
          <label>Área</label>
          <select v-model="create.owner_area">
            <option v-for="a in areas" :key="a.key" :value="a.key">{{ a.label }}</option>
          </select>
        </div>

        <div class="field full">
          <label>Título</label>
          <input v-model.trim="create.title" required />
        </div>

        <div class="field full">
          <label>Descripción</label>
          <textarea v-model.trim="create.description" rows="5" required />
        </div>

        <div class="field">
          <label>Prioridad</label>
          <select v-model="create.priority">
            <option value="LOW">Baja</option>
            <option value="MEDIUM">Media</option>
            <option value="HIGH">Alta</option>
          </select>
        </div>

        <div class="actions full">
          <button class="btn" type="button" @click="goBack">Cancelar</button>
          <button class="btn primary" :disabled="loading" type="submit">
            {{ loading ? 'Creando...' : 'Crear caso' }}
          </button>
        </div>

        <p v-if="error" class="err full">{{ error }}</p>
      </form>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createCase } from '../../services/casesApi'
import { listPublicAreas } from '../../services/adminApi'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const areas = ref([
  { key: 'GENERAL', label: 'General' },
  { key: 'PSYCHOLOGY', label: 'Psicología' },
  { key: 'SOCIAL_WORK', label: 'Trabajo Social' },
  { key: 'MEDICAL', label: 'Médica' }
])

function toKey(name) {
  // Normaliza a MAYUS_SIN_ESPACIOS (máx 32 chars como backend)
  const normalized = (name || '')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toUpperCase()
  return (normalized || 'GENERAL').slice(0, 32)
}

onMounted(async () => {
  try {
    const data = await listPublicAreas()
    if (Array.isArray(data) && data.length) {
      areas.value = data.map((x) => ({
        key: toKey(x.name),
        label: x.name
      }))
      // si el valor actual no existe, toma el primero
      if (!areas.value.some((a) => a.key === create.owner_area)) {
        create.owner_area = areas.value[0].key
      }
    }
  } catch (e) {
    // si admin cae, nos quedamos con el fallback fijo
  }
})

const create = reactive({
  student_id: '',
  owner_area: 'GENERAL',
  title: '',
  description: '',
  priority: 'MEDIUM'
})

function goBack() {
  router.push('/cases')
}

async function onCreate() {
  loading.value = true
  error.value = ''
  try {
    const res = await createCase({ ...create })
    const id = res?.id ?? res?.case_id
    router.push(id ? `/cases/${id}` : '/cases')
  } catch (e) {
    error.value = e?.response?.data?.detail || 'No se pudo crear el caso.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page{
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 16px;
}
.head{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:16px;
  margin-bottom: 16px;
}
.left{
  display:flex;
  gap:12px;
  align-items:flex-start;
}
h1{ margin:0; font-size: 24px; }
.muted{ color:#6b7280; margin-top:4px; }
.err{ color:#b91c1c; margin-top:12px; }

.card{
  background:#fff;
  border:1px solid #e5e7eb;
  border-radius: 16px;
  padding: 16px;
}
.formGrid{
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.field{ display:flex; flex-direction:column; gap:6px; }
.field.full{ grid-column: 1 / -1; }
label{ font-size:12px; color:#6b7280; }
input, select, textarea{
  border:1px solid #e5e7eb;
  border-radius: 12px;
  padding: 10px 12px;
  outline:none;
  background:#fff;
}
textarea{ resize: vertical; }

.actions{
  display:flex;
  justify-content:flex-end;
  gap:10px;
  margin-top: 6px;
}

.btn{
  border:1px solid #e5e7eb;
  background:#fff;
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 700;
  cursor:pointer;
  color:#111827;
}
.btn:hover{ background:#f9fafb; }
.btn.primary{
  background:#2563eb;
  border-color:#2563eb;
  color:#fff;
}
.btn.primary:hover{ filter: brightness(0.97); }

@media (max-width: 720px){
  .formGrid{ grid-template-columns: 1fr; }
}
</style>
