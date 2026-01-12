<template>
  <div class="overlay" @click.self="$emit('close')">
    <div class="modal">
      <header class="head">
        <h3>{{ title }}</h3>
        <button class="x" @click="$emit('close')">✕</button>
      </header>

      <p class="hint">Crea un rango de disponibilidad. Se usará para el calendario semanal.</p>

      <div class="grid">
        <div class="field">
          <label>Área</label>
          <select v-model="form.area">
            <option v-for="a in areasValue" :key="a.key" :value="a.key">{{ a.label }}</option>
          </select>
        </div>

        <div class="field">
          <label>Ubicación</label>
          <input v-model.trim="form.location" placeholder="BIENESTAR_UNIVERSITARIO" />
        </div>

        <div class="field">
          <label>Inicio (fecha y hora)</label>
          <input v-model="form.starts_at" type="datetime-local" />
        </div>

        <div class="field">
          <label>Fin (fecha y hora)</label>
          <input v-model="form.ends_at" type="datetime-local" />
        </div>

        <div class="field" v-if="showProfessionalEmail">
          <label>Professional Email</label>
          <input v-model.trim="form.professional_email" type="email" placeholder="pro@uce.edu.ec" />
          <small class="muted">Solo Admin puede crear slots para otros profesionales.</small>
        </div>
      </div>

      <p v-if="error" class="err">{{ error }}</p>

      <footer class="foot">
        <button class="ghost" @click="$emit('close')">Cancelar</button>
        <button class="btn" @click="submit" :disabled="loading">
          {{ loading ? 'Guardando...' : 'Crear slot' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  title: { type: String, default: 'Nueva disponibilidad' },
  areas: { type: Array, default: () => [] },
  showProfessionalEmail: { type: Boolean, default: false },
  initial: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['close', 'submit'])
const areasValue = computed(() => (props.areas || []).map((x) => (typeof x === 'string' ? { key: x, label: x } : x)))


const loading = ref(false)
const error = ref('')

const form = reactive({
  area: 'PSYCHOLOGY',
  location: 'BIENESTAR_UNIVERSITARIO',
  starts_at: '',
  ends_at: '',
  professional_email: ''
})

watch(
  () => props.initial,
  (v) => {
    if (!v) return
    if (v.area) form.area = v.area
    if (v.location) form.location = v.location
    if (v.starts_at) form.starts_at = v.starts_at
    if (v.ends_at) form.ends_at = v.ends_at
    if (v.professional_email) form.professional_email = v.professional_email
  },
  { immediate: true }
)

function toIso(dtLocal) {
  // datetime-local gives "YYYY-MM-DDTHH:mm"
  if (!dtLocal) return ''
  const d = new Date(dtLocal)
  return d.toISOString()
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const payload = {
      area: form.area,
      location: form.location,
      starts_at: toIso(form.starts_at),
      ends_at: toIso(form.ends_at)
    }
    if (props.showProfessionalEmail && form.professional_email) {
      payload.professional_email = form.professional_email
    }
    await emit('submit', payload)
  } catch (e) {
    error.value = String(e?.message || e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.overlay{
  position:fixed;
  inset:0;
  background: rgba(15,23,42,.55);
  display:flex;
  align-items:center;
  justify-content:center;
  padding: 18px;
  z-index: 50;
}
.modal{
  width: min(720px, 100%);
  background:#fff;
  border-radius: 18px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 20px 70px rgba(0,0,0,.25);
  overflow:hidden;
}
.head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #eef2f7;
}
.head h3{ margin:0; font-size: 16px; font-weight: 900; color:#111827; }
.x{
  border: 1px solid #e5e7eb;
  background:#fff;
  border-radius: 12px;
  padding: 8px 10px;
  cursor:pointer;
}
.hint{ margin: 10px 16px; color:#6b7280; font-size: 13px; }
.grid{
  display:grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding: 0 16px 10px;
}
.field label{ display:block; font-size: 12px; color:#6b7280; font-weight: 800; margin-bottom: 6px;}
.field input, .field select{
  width:100%;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 10px 12px;
  outline:none;
}
.field input:focus, .field select:focus{ border-color:#93c5fd; box-shadow: 0 0 0 4px rgba(59,130,246,.12); }
.muted{ color:#6b7280; font-size: 12px; }
.err{ margin: 0 16px 10px; color:#b91c1c; font-weight: 700; }
.foot{
  display:flex;
  justify-content:flex-end;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid #eef2f7;
  background:#fbfdff;
}
.ghost{
  border: 1px solid #e5e7eb;
  background:#fff;
  padding: 10px 12px;
  border-radius: 12px;
  cursor:pointer;
  font-weight: 800;
}
.btn{
  border: 0;
  background:#2563eb;
  color:#fff;
  padding: 10px 12px;
  border-radius: 12px;
  cursor:pointer;
  font-weight: 900;
}
.btn:disabled{ opacity:.6; cursor:not-allowed; }
@media (max-width: 720px){
  .grid{ grid-template-columns: 1fr; }
}
</style>
