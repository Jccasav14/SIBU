<template>
  <div class="page">
    <header class="head">
      <div class="left">
        <button class="btn" @click="goBack">← Volver</button>
        <div>
          <h1>{{ c?.title || 'Caso' }}</h1>
          <p class="muted" v-if="c">
            Estudiante <b>{{ c.student_id }}</b> • Área <b>{{ c.owner_area }}</b> • ID <b>{{ c.id }}</b>
          </p>
          <p v-if="accessInfo.isShared" class="shareHint">
            Compartido contigo
            <span v-if="accessInfo.permission">(<b>{{ formatPermission(accessInfo.permission) }}</b>)</span>
            <span v-if="accessInfo.via">• vía {{ accessInfo.via }}</span>
          </p>
        </div>
      </div>

      <div class="right" v-if="c">
        <span class="pill">Prioridad: {{ formatPriority(c.priority) }}</span>
        <span class="pill">Estado: {{ formatStatus(c.status) }}</span>
      </div>
    </header>

    <p v-if="loading" class="muted">Cargando caso...</p>
    <p v-if="err" class="err">{{ err }}</p>
    <p v-if="ok" class="ok">{{ ok }}</p>

    <div v-if="c" class="tabs">
      <button class="tab" :class="{ active: tab==='detail' }" @click="tab='detail'">Detalle</button>
      <button class="tab" :class="{ active: tab==='notes' }" @click="openNotes">Notas</button>
      <button class="tab" :class="{ active: tab==='timeline' }" @click="openTimeline">Historial</button>
      <button class="tab" :class="{ active: tab==='share' }" @click="tab='share'">Compartir / Asignar</button>
    </div>

    <!-- ✅ DETALLE -->
    <section v-if="c && tab==='detail'" class="card">
      <div class="grid2">
        <div class="field">
          <label>Título</label>
          <input v-model.trim="edit.title" />
        </div>

        <div class="field">
          <label>Prioridad</label>
          <select v-model="edit.priority">
            <option value="LOW">Baja</option>
            <option value="MEDIUM">Media</option>
            <option value="HIGH">Alta</option>
          </select>
        </div>

        <div class="field full">
          <label>Descripción</label>
          <textarea v-model.trim="edit.description" rows="6" />
        </div>

        <div class="field">
          <label>Estado</label>
          <select v-model="nextStatus">
            <option value="OPEN">Abierto</option>
            <option value="IN_PROGRESS">En atención</option>
            <option value="RESOLVED">Resuelto</option>
            <option value="CLOSED">Cerrado</option>
          </select>
        </div>

        <div class="actions full">
          <button class="btn" :disabled="saving" @click="save">
            {{ saving ? 'Guardando...' : 'Guardar cambios' }}
          </button>
          <button class="btn primary" :disabled="saving" @click="applyStatus">
            Aplicar estado
          </button>
        </div>
      </div>
    </section>

    <!-- ✅ NOTAS -->
    <section v-if="c && tab==='notes'" class="card">
      <div class="cardHead">
        <h2>Notas</h2>
      </div>

      <div class="noteForm">
        <textarea v-model.trim="noteText" rows="3" placeholder="Escribe una nota..." />
        <button class="btn primary" :disabled="addingNote || !noteText" @click="addNote">
          {{ addingNote ? 'Agregando...' : 'Agregar nota' }}
        </button>
      </div>

      <p v-if="notesErr" class="err">{{ notesErr }}</p>

      <div v-if="notesLoading" class="muted">Cargando notas...</div>

      <div v-else class="list">
        <div v-for="n in notes" :key="n.id || n.created_at" class="note">
          <div class="noteTop">
            <b>{{ noteKindLabel(n.kind) }}</b>
            <span class="muted">{{ formatDate(n.created_at) }}</span>
          </div>
          <div class="noteBody">{{ n.content }}</div>
        </div>
        <div v-if="!notes.length" class="muted">Aún no hay notas.</div>
      </div>
    </section>

    <!-- ✅ TIMELINE -->
    <section v-if="c && tab==='timeline'" class="card">
      <div class="cardHead">
        <h2>Historial</h2>
        <button class="btn" @click="reloadTimeline">Recargar</button>
      </div>

      <p v-if="timelineErr" class="err">{{ timelineErr }}</p>
      <p v-if="timelineLoading" class="muted">Cargando historial...</p>

      <div v-else class="list">
        <div v-for="t in timeline" :key="t.id || t.at" class="timelineRow">
          <div class="timelineTop">
            <b>{{ timelineView(t).title }}</b>
            <span class="muted">{{ formatDate(t.at || t.created_at) }}</span>
          </div>
          <div class="timelineBody">{{ timelineView(t).message }}</div>
        </div>
        <div v-if="!timeline.length" class="muted">Sin historial por ahora.</div>
      </div>
    </section>

    <!-- ✅ SHARE / ASSIGN -->
    <section v-if="c && tab==='share'" class="card">
      <div class="cardHead">
        <h2>Permisos</h2>
        <p class="muted">Comparte el caso con otros profesionales o áreas. (El backend valida permisos.)</p>
      </div>

      <div class="shareActions">
        <button class="btn primary" @click="openShare = true">Compartir caso</button>
        <button v-if="isAdmin" class="btn" @click="openAssign = true">Asignar profesional</button>
      </div>

      <ShareCaseModal v-if="openShare" :case-id="caseId" @close="openShare=false" @submit="onShare" />
      <AssignCaseModal v-if="openAssign" :case-id="caseId" @close="openAssign=false" @submit="onAssign" />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { auth } from '../../stores/auth'
import {
  getCase,
  updateCase,
  assignCase,
  changeCaseStatus,
  shareCase,
  addCaseNote,
  listCaseNotes,
  getCaseTimeline
} from '../../services/casesApi'
import ShareCaseModal from '../../components/cases/ShareCaseModal.vue'
import AssignCaseModal from '../../components/cases/AssignCaseModal.vue'
import { formatPriority, formatStatus, formatPermission, formatTimelineEvent, normalizeEnum, formatArea } from '../../utils/caseFormatters'

const route = useRoute()
const router = useRouter()
const caseId = computed(() => route.params.id)

const currentUserId = computed(() => auth.user()?.id || auth.user()?.user_id || auth.user()?.sub || '')
const currentArea = computed(() => auth.user()?.area || '')
const isAdmin = computed(() => String(auth.user()?.role || '').toLowerCase() === 'admin')

const accessInfo = ref({
  isShared: false,
  permission: '',
  sharedBy: '',
  via: ''
})

const tab = ref('detail')

const loading = ref(false)
const saving = ref(false)
const err = ref('')
const ok = ref('')

const c = ref(null)
const edit = ref({ title: '', description: '', priority: 'MEDIUM' })
const nextStatus = ref('OPEN')

// Notes
const notes = ref([])
const notesLoading = ref(false)
const notesErr = ref('')
const noteText = ref('')
const addingNote = ref(false)

// Timeline
const timeline = ref([])
const timelineLoading = ref(false)
const timelineErr = ref('')

// Modals
const openShare = ref(false)
const openAssign = ref(false)

function goBack() {
  router.push('/cases')
}

function formatDate(d) {
  if (!d) return ''
  try {
    return new Date(d).toLocaleString()
  } catch {
    return String(d)
  }
}

function timelineView(t) {
  return formatTimelineEvent(t)
}

function noteKindLabel(kind) {
  const k = normalizeEnum(kind || 'NOTE')
  if (k === 'NOTE') return 'Nota'
  if (k === 'OBSERVATION') return 'Observación'
  if (k === 'ALERT') return 'Alerta'
  return k
}

async function loadCase() {
  err.value = ''
  ok.value = ''
  loading.value = true
  try {
    c.value = await getCase(caseId.value)
    edit.value = {
      title: c.value.title,
      description: c.value.description,
      priority: c.value.priority
    }
    nextStatus.value = c.value.status
    // Pre-cargamos el historial para poder mostrar si el caso fue compartido contigo.
    await reloadTimeline()
  } catch (e) {
    err.value = e?.message || 'Error cargando caso'
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!c.value) return
  ok.value = ''
  err.value = ''
  saving.value = true
  try {
    const updated = await updateCase(c.value.id, { ...edit.value })
    c.value = updated
    ok.value = 'Cambios guardados.'
  } catch (e) {
    err.value = e?.message || 'No se pudieron guardar los cambios.'
  } finally {
    saving.value = false
  }
}

async function applyStatus() {
  if (!c.value) return
  ok.value = ''
  err.value = ''
  saving.value = true
  try {
    const updated = await changeCaseStatus(c.value.id, nextStatus.value)
    c.value = updated
    ok.value = 'Estado actualizado.'
    await reloadTimeline()
  } catch (e) {
    err.value = e?.message || 'No se pudo actualizar el estado.'
  } finally {
    saving.value = false
  }
}

function deriveAccessFromTimeline() {
  // Intentamos inferir si este caso fue compartido contigo (por USER o por AREA) y el permiso.
  // El backend no devuelve access en CaseOut, pero sí registra SHARED en timeline.
  const uid = currentUserId.value
  const area = currentArea.value
  if (!uid && !area) {
    accessInfo.value = { isShared: false, permission: '', sharedBy: '', via: '' }
    return
  }
  const sharedEvents = (timeline.value || []).filter((t) => (t.type || t.event) === 'SHARED')
  // Tomamos el más reciente que coincida con user_id o area
  const match = [...sharedEvents].reverse().find((t) => {
    const data = t.data || {}
    return (data.user_id && String(data.user_id) === String(uid)) || (data.area && area && String(data.area) === String(area))
  })
  if (!match) {
    accessInfo.value = { isShared: false, permission: '', sharedBy: '', via: '' }
    return
  }
  const data = match.data || {}
  accessInfo.value = {
    isShared: true,
    permission: data.permission || '',
    sharedBy: match.actor_user_id || '',
    via: data.user_id ? 'usuario' : (data.area ? `área ${formatArea(data.area)}` : '')
  }
}

async function reloadNotes() {
  notesErr.value = ''
  notesLoading.value = true
  try {
    const res = await listCaseNotes(caseId.value)
    notes.value = res?.items ?? res ?? []
  } catch (e) {
    notesErr.value = e?.message || 'Error cargando notas.'
  } finally {
    notesLoading.value = false
  }
}

async function addNote() {
  if (!noteText.value) return
  addingNote.value = true
  notesErr.value = ''
  try {
    await addCaseNote(caseId.value, { kind: 'NOTE', content: noteText.value })
    noteText.value = ''
    await reloadNotes()
    await reloadTimeline()
  } catch (e) {
    notesErr.value = e?.message || 'No se pudo agregar la nota.'
  } finally {
    addingNote.value = false
  }
}

async function reloadTimeline() {
  timelineErr.value = ''
  timelineLoading.value = true
  try {
    const res = await getCaseTimeline(caseId.value)
    timeline.value = res?.items ?? res ?? []
    deriveAccessFromTimeline()
  } catch (e) {
    timelineErr.value = e?.message || 'Error cargando historial.'
  } finally {
    timelineLoading.value = false
  }
}

function openNotes() {
  tab.value = 'notes'
  if (!notes.value.length) reloadNotes()
}

function openTimeline() {
  tab.value = 'timeline'
  if (!timeline.value.length) reloadTimeline()
}

// Share / Assign
async function onShare(payload) {
  ok.value = ''
  err.value = ''
  try {
    await shareCase(caseId.value, payload)
    ok.value = 'Caso compartido.'
    openShare.value = false
    await reloadTimeline()
  } catch (e) {
    err.value = e?.message || 'No se pudo compartir el caso.'
  }
}

async function onAssign(payload) {
  ok.value = ''
  err.value = ''
  try {
    await assignCase(caseId.value, payload)
    ok.value = 'Caso asignado.'
    openAssign.value = false
    await loadCase()
  } catch (e) {
    err.value = e?.message || 'No se pudo asignar el caso.'
  }
}

onMounted(loadCase)
</script>

<style scoped>
.page{
  /* el ancho y padding lo maneja el layout global */
  padding: 0;
}
.head{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:16px;
  margin-bottom: 12px;
}
.left{
  display:flex;
  gap:12px;
  align-items:flex-start;
}
.right{ display:flex; gap:8px; align-items:center; }
h1{ margin:0; font-size: 24px; }
.muted{ color:#6b7280; margin-top:4px; }
.shareHint{
  margin: 6px 0 0;
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 13px;
}
.err{ color:#b91c1c; margin-top:12px; }
.ok{ color:#065f46; margin-top:12px; }

.pill{
  border:1px solid #e5e7eb;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 800;
  color:#374151;
  background:#fff;
}

.tabs{
  display:flex;
  gap:8px;
  margin: 12px 0 16px;
}
.tab{
  border: 1px solid #e5e7eb;
  background:#fff;
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 800;
  color:#374151;
  cursor:pointer;
}
.tab.active{
  background:#eff6ff;
  border-color:#bfdbfe;
  color:#2563eb;
}
.tab:hover{ background:#f9fafb; }

.card{
  background:#fff;
  border:1px solid #e5e7eb;
  border-radius: 16px;
  padding: 16px;
}
.cardHead{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:12px;
  margin-bottom: 12px;
}
.cardHead h2{ margin:0; font-size: 18px; }
.grid2{
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap:12px;
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

.list{ display:flex; flex-direction:column; gap:10px; }
.note, .timelineRow{
  border:1px solid #e5e7eb;
  border-radius: 14px;
  padding: 12px;
}
.noteTop, .timelineTop{
  display:flex;
  justify-content:space-between;
  gap:10px;
  margin-bottom: 6px;
}
.noteBody, .timelineBody{ color:#111827; white-space: pre-wrap; }

.noteForm{
  display:flex;
  gap:10px;
  align-items:flex-start;
  margin-bottom: 12px;
}
.noteForm textarea{ flex:1; }

.shareActions{
  display:flex;
  gap:10px;
  flex-wrap:wrap;
}

.btn{
  border:1px solid #e5e7eb;
  background:#fff;
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 800;
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
  .head{ flex-direction:column; align-items:stretch; }
  .grid2{ grid-template-columns: 1fr; }
  .noteForm{ flex-direction:column; }
}
</style>
