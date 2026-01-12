<template>
  <div class="layout">
    <aside class="side">
      <div class="card">
        <div class="sideHead">
          <h3>Profesionales</h3>
          <button class="ghost" @click="loadProfessionals" :disabled="loadingPros">
            {{ loadingPros ? '...' : 'Recargar' }}
          </button>
        </div>

        <div class="search">
          <input v-model.trim="q" placeholder="Buscar por email o nombre..." />
        </div>

        <div class="list">
          <button
            class="item"
            :class="{ active: selectedEmail === null }"
            @click="select(null)"
          >
            <div class="pill all">Todos</div>
            <div class="meta">Vista global</div>
          </button>

          <button
            v-for="p in filteredPros"
            :key="p.email"
            class="item"
            :class="{ active: selectedEmail === p.email }"
            @click="select(p.email)"
          >
            <div class="pill">PRO</div>
            <div class="meta">
              <div class="email">{{ p.email }}</div>
              <div class="name" v-if="p.full_name">{{ p.full_name }}</div>
            </div>
          </button>
        </div>

        <div class="manual">
          <label>O ingresar email manual</label>
          <div class="row">
            <input v-model.trim="manualEmail" placeholder="pro@uce.edu.ec" />
            <button class="btn" @click="select(manualEmail)" :disabled="!manualEmail">Ver</button>
          </div>
          <small class="muted">Si el servicio users no expone listado, igual puedes entrar por email.</small>
        </div>
      </div>

      <div class="card filters">
        <h3>Filtros</h3>

        <div class="field">
          <label>Cédula / student_id</label>
          <input v-model.trim="studentIdFilter" placeholder="Ej: 1751360999" />
        </div>

        <div class="field">
          <label>Área</label>
          <select v-model="area">
            <option value="">Todas</option>
            <option v-for="a in areas" :key="a" :value="a">{{ a }}</option>
          </select>
        </div>

        <div class="field">
          <label>Semana</label>
          <div class="weekRow">
            <button class="ghost" @click="prevWeek">‹</button>
            <div class="weekLabel">{{ weekLabel }}</div>
            <button class="ghost" @click="nextWeek">›</button>
          </div>
        </div>

        <button class="btn full" @click="openCreateSlot">+ Nueva disponibilidad</button>
      </div>
    </aside>

    <main class="main">
      <div class="topBar">
        <div class="context">
          <div class="k">Viendo:</div>
          <div class="v">{{ selectedEmail ? selectedEmail : 'Todos los profesionales' }}</div>
        </div>

        <div class="right">
          <button class="ghost" @click="refresh" :disabled="loading">
            {{ loading ? 'Cargando...' : 'Actualizar' }}
          </button>
        </div>
      </div>

      <WeekCalendar
        title="Calendario semanal"
        :subtitle="calendarSubtitle"
        :weekStart="weekStart"
        :slots="slots"
        :appointmentsBySlotId="appointmentsBySlotId"
        @prev="prevWeek"
        @next="nextWeek"
        @today="goToday"
        @blockClick="onBlockClick"
      />

      <div class="panel">
        <h3>Acciones rápidas</h3>
        <p class="muted">
          Haz click en un bloque <b>Disponible</b> para crear una cita.
          Haz click en un bloque <b>Ocupado</b> para ver detalle (MVP).
        </p>
      </div>
    </main>

    <SlotFormModal
      v-if="showSlotModal"
      :showProfessionalEmail="true"
      :initial="slotInitial"
      :areas="areas"
      
      @close="closeSlotModal"
      @submit="submitSlot"
    />

    <AppointmentFormModal
      v-if="showApptModal"
      :slot="apptSlot"
      :errorText="apptError"
      @close="closeAppt"
      @submit="submitAppointment"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import WeekCalendar from '../../components/agenda/WeekCalendar.vue'
import SlotFormModal from '../../components/agenda/SlotFormModal.vue'
import AppointmentFormModal from '../../components/agenda/AppointmentFormModal.vue'
import { listAvailability, createAvailability, createAppointment, listAppointmentsMine } from '../../services/appointmentsApi'
import { listPublicAreas } from '../../services/adminApi'
import { listUsers } from '../../services/usersApi'

const areas = ref([])
const q = ref('')
const manualEmail = ref('')
const selectedEmail = ref(null)

const pros = ref([])
const loadingPros = ref(false)

const area = ref('')
const studentIdFilter = ref('')

const weekStart = ref(startOfWeek(new Date()))
const loading = ref(false)
const error = ref('')

const slots = ref([])
const appointmentsBySlotId = ref({})

const showSlotModal = ref(false)
const editSlotId = ref(null)
const slotInitial = ref({})
const showApptModal = ref(false)
const apptError = ref('')
const apptSlot = ref(null)

const weekLabel = computed(() => {
  const d0 = new Date(weekStart.value)
  const d6 = new Date(d0); d6.setDate(d0.getDate() + 6)
  const a = d0.toLocaleDateString('es-EC', { day:'2-digit', month:'short' })
  const b = d6.toLocaleDateString('es-EC', { day:'2-digit', month:'short' })
  return `${a} – ${b}`
})

const calendarSubtitle = computed(() => {
  const a = area.value ? `Área: ${area.value}` : 'Todas las áreas'
  return `${a} · ${weekLabel.value}`
})

const filteredPros = computed(() => {
  const needle = q.value.toLowerCase()
  return (pros.value || []).filter(p => {
    const s = `${p.email} ${p.full_name || ''}`.toLowerCase()
    return s.includes(needle)
  })
})

function startOfWeek(date){
  const d = new Date(date)
  const day = (d.getDay() + 6) % 7 // monday=0
  d.setHours(0,0,0,0)
  d.setDate(d.getDate() - day)
  return d
}

function rangeISO(){
  const from = new Date(weekStart.value)
  const to = new Date(from); to.setDate(from.getDate() + 7)
  return { from: from.toISOString(), to: to.toISOString() }
}

async function loadProfessionals(){
  loadingPros.value = true
  try{
    // best-effort: if the endpoint doesn't exist, we keep empty list and allow manual email
    const data = await listUsers({ role: 'professional' })
    // expected: [{email, full_name, role, active}]
    pros.value = Array.isArray(data) ? data : (data.items || [])
  }catch(e){
    pros.value = []
  }finally{
    loadingPros.value = false
  }
}

function select(email){
  selectedEmail.value = email || null
  refresh()
}

async function refresh(){
  loading.value = true
  error.value = ''
  try{
    const { from, to } = rangeISO()
    const params = {
      from,
      to,
      only_open: false
    }
    if (area.value) params.area = area.value
    if (selectedEmail.value) params.professional_email = selectedEmail.value

    const av = await listAvailability(params)
    slots.value = Array.isArray(av) ? av : (av.items || [])

    // appointments for the same range to show student_id/status
    const apParams = { from, to }
    if (area.value) apParams.area = area.value
    if (selectedEmail.value) apParams.professional_email = selectedEmail.value
    const ap = await listAppointmentsMine(apParams)
    const list = Array.isArray(ap) ? ap : (ap.items || [])
    const map = {}
    for (const a of list){
      if (a.slot_id) map[a.slot_id] = a
      if (a.slot?.id) map[a.slot.id] = a
    }
    appointmentsBySlotId.value = map
  }catch(e){
    error.value = String(e?.message || e)
  }finally{
    loading.value = false
  }
}

function prevWeek(){
  const d = new Date(weekStart.value); d.setDate(d.getDate()-7)
  weekStart.value = startOfWeek(d)
  refresh()
}
function nextWeek(){
  const d = new Date(weekStart.value); d.setDate(d.getDate()+7)
  weekStart.value = startOfWeek(d)
  refresh()
}
function goToday(){
  weekStart.value = startOfWeek(new Date())
  refresh()
}

function openCreateSlot(){
  showSlotModal.value = true
  slotInitial.value = { professional_email: selectedEmail.value || manualEmail.value || '' }
}

async function submitSlot(payload){
  // payload already ISO
  if (!payload.professional_email && selectedEmail.value) payload.professional_email = selectedEmail.value
  await createAvailability(payload)
  closeSlotModal()
  await refresh()
}

async function onBlockClick(block){
  const slot = block?.raw?.slot
  const appt = block?.raw?.appointment
  if(!slot) return

  if (appt) return
  if(slot.is_booked) return

  const choice = window.prompt('Acción: 1=Asignar estudiante, 2=Editar, 3=Eliminar', '1')

  if (choice === '3'){
    if (window.confirm('¿Eliminar este slot de disponibilidad?')){
      await deleteAvailability(slot.id)
      await refresh()
    }
    return
  }

  if (choice === '2'){
    editSlotId.value = slot.id
    slotInitial.value = {
      professional_email: selectedEmail.value || '',
      area: slot.area,
      location: slot.location,
      starts_at: slot.starts_at,
      ends_at: slot.ends_at,
    }
    showSlotModal.value = true
    return
  }

  apptSlot.value = slot
  showApptModal.value = true
}


function closeAppt(){
  showApptModal.value = false
  apptError.value = ''
  apptSlot.value = null
}

async function submitAppointment(payload){
  apptError.value = ''
  // basic duplicate prevention on same professional+starts_at (backend should enforce)
  const existing = appointments.value?.find?.(a => a?.starts_at === payload?.starts_at && a?.professional_email === payload?.professional_email && String(a?.status || '').toUpperCase() !== 'CANCELED')
  if (existing){
    apptError.value = 'Este horario ya está ocupado.'
    return
  }
  try{
    const created = await createAppointment(payload)

    if (created){
      const prev = Array.isArray(appointments.value) ? appointments.value : []
      const id = created.id
      appointments.value = id ? [...prev.filter(a => a?.id !== id), created] : [...prev, created]
      const slotId = created.slot_id || created.availability_id || created.slot?.id
      if (slotId && Array.isArray(slots.value)){
        const s = slots.value.find(x => x?.id === slotId)
        if (s) s.is_booked = true
      }
    }

    closeAppt()
    await refresh()
  } catch (e){
    apptError.value = String(e?.message || e)
  }
}

onMounted(async () => {
  await loadAreas()

  await loadProfessionals()
  await refresh()
})
</script>

<style scoped>
.layout{
  display:grid;
  grid-template-columns: 360px 1fr;
  gap: 14px;
  align-items:start;
}
.side{ position: sticky; top: 16px; }
.card{
  background:#fff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(0,0,0,.06);
  padding: 14px;
}
.sideHead{
  display:flex; align-items:center; justify-content:space-between; gap: 10px;
}
h3{ margin:0; font-size: 14px; font-weight: 900; color:#111827; }
.search{ margin-top: 10px; }
.search input{
  width:100%;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 10px 12px;
  outline:none;
}
.search input:focus{ border-color:#93c5fd; box-shadow: 0 0 0 4px rgba(59,130,246,.12); }

.list{
  margin-top: 10px;
  display:flex;
  flex-direction:column;
  gap: 8px;
  max-height: 320px;
  overflow:auto;
  padding-right: 4px;
}
.item{
  display:flex;
  gap: 10px;
  align-items:flex-start;
  padding: 10px 10px;
  border-radius: 16px;
  border: 1px solid #eef2f7;
  background:#fff;
  cursor:pointer;
  text-align:left;
}
.item:hover{ background:#fbfdff; border-color:#dbeafe; }
.item.active{ background:#eff6ff; border-color:#93c5fd; }
.pill{
  background:#111827;
  color:#fff;
  font-weight: 900;
  font-size: 11px;
  border-radius: 999px;
  padding: 6px 8px;
}
.pill.all{ background:#6b7280; }
.meta{ min-width: 0; }
.email{ font-weight: 900; color:#111827; font-size: 12px; overflow:hidden; text-overflow:ellipsis; }
.name{ color:#6b7280; font-size: 12px; margin-top: 2px; }

.manual{ margin-top: 12px; border-top: 1px solid #eef2f7; padding-top: 12px; }
.manual label{ display:block; font-size: 12px; color:#6b7280; font-weight: 800; margin-bottom: 6px; }
.row{ display:flex; gap: 8px; }
.row input{
  flex:1;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 10px 12px;
}
.filters{ margin-top: 12px; }
.field{ margin-top: 10px; }
.field label{ display:block; font-size: 12px; color:#6b7280; font-weight: 800; margin-bottom: 6px; }
.field select{
  width:100%;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 10px 12px;
}
.weekRow{ display:flex; gap: 10px; align-items:center; justify-content:space-between; }
.weekLabel{ font-weight: 900; color:#111827; font-size: 13px; }
.ghost{
  border: 1px solid #e5e7eb;
  background:#fff;
  padding: 8px 10px;
  border-radius: 12px;
  cursor:pointer;
  font-weight: 900;
}
.btn{
  border:0;
  background:#2563eb;
  color:#fff;
  padding: 10px 12px;
  border-radius: 14px;
  cursor:pointer;
  font-weight: 900;
}
.btn.full{ width:100%; margin-top: 12px; }
.muted{ color:#6b7280; font-size: 12px; }

.main{ min-width: 0; display:flex; flex-direction:column; gap: 12px; }
.topBar{
  display:flex; align-items:center; justify-content:space-between; gap: 12px;
  background:#fff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 12px 14px;
  box-shadow: 0 10px 30px rgba(0,0,0,.06);
}
.context{ display:flex; gap: 8px; align-items:center; min-width:0; }
.k{ color:#6b7280; font-weight: 800; font-size: 12px; }
.v{ color:#111827; font-weight: 900; font-size: 13px; overflow:hidden; text-overflow:ellipsis; }
.panel{
  background:#fff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 14px;
  box-shadow: 0 10px 30px rgba(0,0,0,.06);
}
.panel p{ margin: 8px 0 0; }
@media (max-width: 1100px){
  .layout{ grid-template-columns: 1fr; }
  .side{ position: static; }
}
</style>
