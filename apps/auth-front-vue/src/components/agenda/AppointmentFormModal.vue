<template>
  <div class="overlay" v-if="isOpen" @click.self="$emit('close')">
    <div class="modal">
      <header class="head">
        <h3>Asignar cita</h3>
        <button class="x" @click="$emit('close')">✕</button>
      </header>

      <div class="info">
        <div class="pill">Hora</div>
        <div class="meta">
          <div class="when">{{ pretty(isoValue) }}</div>
          <div class="muted">Bloque de 30 minutos (07:00–19:00)</div>
        </div>
      </div>

      <div class="field">
        <label>Área</label>
        <select v-model="area">
          <option v-for="a in areasValue" :key="a.key" :value="a.key">{{ a.label }}</option>
        </select>
      </div>

      <div class="field">
        <label>Cédula / Student ID</label>
        <input v-model.trim="student_id" placeholder="Ej: 1751360999" />
      </div>

      <p v-if="error" class="err">{{ error }}</p>

      <footer class="foot">
        <button class="ghost" @click="$emit('close')" :disabled="loading">Cancelar</button>
        <button class="btn" @click="submit" :disabled="loading || !student_id">
          {{ loading ? 'Guardando...' : 'Confirmar' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  errorText: { type: String, default: '' },
  open: { type: Boolean, default: false },
  iso: { type: String, default: '' },
  areas: { type: Array, default: () => [] },
  slot: { type: Object, default: null },
  onSubmit: { type: Function, default: null }
})

const emit = defineEmits(['close', 'submit'])

// NOTE: do NOT reference isOpen.value inside itself (causes infinite recursion / UI freeze)
const isOpen = computed(() => !!props.open || !!props.slot)
const isoValue = computed(() => props.iso || props.slot?.starts_at || '')
const areasValue = computed(() => (props.areas && props.areas.length ? props.areas : (props.slot?.area ? [props.slot.area] : [])))


const student_id = ref('')
const area = ref('')
const error = ref('')
const loading = ref(false)

watch(
  () => isOpen.value,
  (v) => {
    if (v) {
      // reset each open
      student_id.value = ''
      error.value = props.errorText || ''
      area.value = areasValue.value?.[0]?.key || ''
      loading.value = false
    }
  }
)

watch(
  () => props.errorText,
  (v) => {
    if (isOpen.value && v) error.value = v
  }
)

function pretty(iso) {
  const d = new Date(iso)
  return d.toLocaleString('es-EC', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function submit() {
  error.value = ''
  if (!isoValue.value) {
    error.value = 'Hora inválida'
    return
  }
  if (!area.value) {
    error.value = 'Selecciona un área'
    return
  }
  if (!student_id.value) {
    error.value = 'Ingresa la cédula'
    return
  }

  loading.value = true
  try {
    // Backend accepts starts_at booking mode (will create/find 30-min slot and reserve)
    const payload = {
      starts_at: isoValue.value,
      area: area.value,
      student_id: student_id.value,
    }

    if (props.onSubmit) {
      await props.onSubmit(payload)
    } else {
      emit('submit', payload)
    }
    // close only on success
    emit('close')
  } catch (e) {
    error.value = String(e?.message || e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.overlay{
  position: fixed; inset:0; background: rgba(15,23,42,.45);
  display:flex; align-items:center; justify-content:center;
  padding: 24px; z-index: 50;
}
.modal{
  width: min(520px, 100%);
  background:#fff;
  border-radius: 18px;
  box-shadow: 0 18px 60px rgba(2,6,23,.35);
  overflow:hidden;
}
.head{
  display:flex; align-items:center; justify-content:space-between;
  padding: 14px 16px;
  border-bottom:1px solid #eef2f7;
  background: linear-gradient(180deg, #fbfdff, #fff);
}
.head h3{ margin:0; font-size: 16px; font-weight: 900; }
.x{
  border:0; background:transparent; cursor:pointer;
  font-size: 16px; padding: 6px 10px; border-radius: 10px;
}
.x:hover{ background:#f1f5f9; }
.info{
  display:flex; gap: 12px; padding: 14px 16px;
  border-bottom:1px dashed #e5e7eb;
  background:#fcfdff;
}
.pill{
  background:#111827; color:#fff; font-weight: 900;
  padding: 6px 10px; border-radius: 999px; font-size: 12px;
  height: fit-content;
}
.meta .when{ font-weight: 900; }
.field{ padding: 12px 16px; display:flex; flex-direction:column; gap:6px; }
.field label{ font-size: 12px; font-weight: 900; color:#374151; }
.field input, .field select{
  border:1px solid #e5e7eb; border-radius: 12px;
  padding: 10px 12px; outline:none;
}
.field input:focus, .field select:focus{
  border-color:#93c5fd; box-shadow: 0 0 0 4px rgba(59,130,246,.12);
}
.muted{ color:#6b7280; font-size: 12px; }
.err{ margin: 0 16px 10px; color:#b91c1c; font-weight: 800; }
.foot{
  display:flex; justify-content:flex-end; gap: 10px;
  padding: 12px 16px; border-top: 1px solid #eef2f7; background:#fbfdff;
}
.ghost{
  border: 1px solid #e5e7eb; background:#fff;
  padding: 10px 12px; border-radius: 12px;
  cursor:pointer; font-weight: 900;
}
.btn{
  border:0; background:#2563eb; color:#fff;
  padding: 10px 12px; border-radius: 12px;
  cursor:pointer; font-weight: 900;
}
.btn:disabled, .ghost:disabled{ opacity:.6; cursor:not-allowed; }
</style>