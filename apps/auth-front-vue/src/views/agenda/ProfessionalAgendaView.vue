<template>
  <div class="layout">
    <div class="topBar">
      <div class="left">
        <h2>Mi agenda</h2>
        <p class="muted">Semana · 07:00–19:00 · Click en una celda para asignar una cita</p>
      </div>

      <div class="right">
        <button class="ghost" @click="refresh" :disabled="loading">
          {{ loading ? 'Cargando...' : 'Actualizar' }}
        </button>
      </div>
    </div>

    <WeekCalendar
      title="Calendario semanal"
      :subtitle="weekLabel"
      :weekStart="weekStart"
      :slots="slots"
      :appointmentsBySlotId="appointmentsBySlotId"
      @prev="prevWeek"
      @next="nextWeek"
      @today="goToday"
      @cellClick="onCellClick"
      @blockClick="onBlockClick"
    />

    <AppointmentFormModal
      :open="showApptModal"
      :iso="apptIso"
      :areas="areas"
      :errorText="apptError"
      @close="closeApptModal"
      :onSubmit="submitAppt"
      />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import WeekCalendar from '../../components/agenda/WeekCalendar.vue'
import AppointmentFormModal from '../../components/agenda/AppointmentFormModal.vue'
import { listAvailability, listAppointmentsMine, createAppointment } from '../../services/appointmentsApi'
const NAME_TO_ENUM = {
  // Español -> enum backend
  'PSICOLOGIA': 'PSYCHOLOGY',
  'PSICOLOGÍA': 'PSYCHOLOGY',
  'TRABAJO_SOCIAL': 'SOCIAL_WORK',
  'TRABAJO SOCIAL': 'SOCIAL_WORK',
  'MEDICA': 'MEDICINE',
  'MÉDICA': 'MEDICINE',
  'ACADEMICA': 'ACADEMIC',
  'ACADÉMICA': 'ACADEMIC',
  'LEGAL': 'LEGAL'
}

const APPOINTMENT_AREA_KEYS = ["PSYCHOLOGY", "SOCIAL_WORK", "MEDICINE", "ACADEMIC", "LEGAL"]

function toKey(name) {
  const normalized = (name || '')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toUpperCase()
  return (normalized || 'PSYCHOLOGY').slice(0, 32)
}

async function loadAreas() {
  // fallback local (mismo enum del backend de appointments)
  const fallback = [
    { key: 'PSYCHOLOGY', label: 'Psicología' },
    { key: 'SOCIAL_WORK', label: 'Trabajo Social' },
    { key: 'MEDICINE', label: 'Médica' },
    { key: 'ACADEMIC', label: 'Académica' },
    { key: 'LEGAL', label: 'Legal' },
  ]

  try {
    const data = await listPublicAreas()
    if (Array.isArray(data) && data.length) {
      const mapped = data
        .map((x) => {
          const raw = (x?.name || '').trim()
          const k = toKey(raw)
          const enumKey = NAME_TO_ENUM[k] || k
          return { key: enumKey, label: raw || enumKey }
        })
        .filter((x) => APPOINTMENT_AREA_KEYS.includes(x.key))

      if (mapped.length) {
        areas.value = mapped
        return
      }
    }
  } catch (e) {
    // degradado: usamos fallback
  }

  areas.value = fallback
}


import { listPublicAreas } from '../../services/adminApi'

const areas = ref([])
const loading = ref(false)
const weekStart = ref(startOfWeek(new Date()))
const slots = ref([])
const appointments = ref([])

const showApptModal = ref(false)
const apptError = ref('')
const apptIso = ref('')

const weekLabel = computed(() => {
  const d0 = new Date(weekStart.value)
  const d6 = new Date(d0); d6.setDate(d0.getDate() + 6)
  const a = d0.toLocaleDateString('es-EC', { day:'2-digit', month:'short' })
  const b = d6.toLocaleDateString('es-EC', { day:'2-digit', month:'short' })
  return `${a} – ${b}`
})

const appointmentsBySlotId = computed(() => {
  const map = {}
  for (const a of appointments.value || []) {
    if (a?.slot_id) map[a.slot_id] = a
  }
  return map
})

function startOfWeek(date){
  const d = new Date(date)
  const day = (d.getDay() + 6) % 7 // monday=0
  d.setHours(0,0,0,0)
  d.setDate(d.getDate() - day)
  return d
}

function rangeForWeek(){
  const from = new Date(weekStart.value)
  const to = new Date(from); to.setDate(from.getDate() + 6)
  from.setHours(0,0,0,0)
  to.setHours(23,59,59,999)
  return { from: from.toISOString(), to: to.toISOString() }
}

async function refresh(){
  loading.value = true
  try {
    const r = rangeForWeek()
    const [av, ap] = await Promise.all([
      listAvailability({ from: r.from, to: r.to }),
      listAppointmentsMine({ from: r.from, to: r.to }),
    ])
    slots.value = Array.isArray(av) ? av : []
    appointments.value = Array.isArray(ap) ? ap : []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function prevWeek(){
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() - 7)
  weekStart.value = startOfWeek(d)
  refresh()
}
function nextWeek(){
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + 7)
  weekStart.value = startOfWeek(d)
  refresh()
}
function goToday(){
  weekStart.value = startOfWeek(new Date())
  refresh()
}

function onCellClick({ dayKey, time }) {
  const local = new Date(`${dayKey}T${time}:00`)
  apptIso.value = local.toISOString()
  apptError.value = ''
  showApptModal.value = true
}

function onBlockClick(block) {
  const s = block?.raw?.slot
  if (s?.starts_at) {
    apptIso.value = new Date(s.starts_at).toISOString()
    showApptModal.value = true
  }
}

function closeApptModal(){
  showApptModal.value = false
  apptError.value = ''
  apptIso.value = ''
}

async function submitAppt(payload){
  apptError.value = ''

  // Prevent duplicates client-side (backend should also enforce)
  const existing = (appointments.value || []).find(
    (a) =>
      a?.starts_at === payload?.starts_at &&
      String(a?.status || '').toUpperCase() !== 'CANCELED'
  )
  if (existing){
    throw new Error('Este horario ya está ocupado.')
  }

  const created = await createAppointment(payload)

  // Optimistic UI update so it appears immediately
  if (created){
    const prev = Array.isArray(appointments.value) ? appointments.value : []
    const id = created.id
    appointments.value = id ? [...prev.filter(a => a?.id !== id), created] : [...prev, created]

    // mark slot booked (if we have the slot)
    const slotId = created.slot_id || created.availability_id || created.slot?.id
    if (slotId && Array.isArray(slots.value)){
      const s = slots.value.find(x => x?.id === slotId)
      if (s) s.is_booked = true
    }
  }

  refresh().catch(()=>{})
  return created
}


onMounted(async () => {
  await loadAreas()
  await refresh()
})
</script>

<style scoped>
.layout{ display:flex; flex-direction:column; gap: 14px; }
.topBar{
  display:flex; align-items:flex-end; justify-content:space-between;
  gap: 12px;
}
.left h2{ margin:0; font-weight: 950; }
.muted{ margin: 2px 0 0; color:#6b7280; font-size: 12px; }
.right{ display:flex; gap: 10px; }
.ghost{
  border:1px solid #e5e7eb; background:#fff;
  padding: 10px 12px; border-radius: 12px;
  font-weight: 900; cursor:pointer;
}
.ghost:disabled{ opacity:.6; cursor:not-allowed; }
</style>
