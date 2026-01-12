<template>
  <div class="page">
    <header class="head">
      <div>
        <h1>Casos</h1>
        <p class="muted">Gestiona tus casos, busca por estudiante y accede al detalle para asignar, compartir y registrar notas.</p>
      </div>

      <div class="actions">
        <button class="btn" @click="refresh" :disabled="loadingMine || loadingStudent">Recargar</button>
        <RouterLink class="btn primary" to="/cases/new">+ Nuevo caso</RouterLink>
      </div>
    </header>

    <div class="tabs">
      <button class="tab" :class="{ active: tab==='mine' }" @click="tab='mine'">Mis casos</button>
      <button v-if="isProfessional" class="tab" :class="{ active: tab==='shared' }" @click="openShared">Compartidos conmigo</button>
      <button class="tab" :class="{ active: tab==='student' }" @click="tab='student'">Por estudiante</button>
    </div>

    <!-- ✅ MIS CASOS -->
    <section v-if="tab==='mine'" class="card">
      <div class="cardHead">
        <h2>Mis casos</h2>
        <div class="filters">
          <select v-model="mineFilters.status" @change="loadMine">
            <option value="">Estado (todos)</option>
            <option value="OPEN">Abierto</option>
            <option value="IN_PROGRESS">En atención</option>
            <option value="RESOLVED">Resuelto</option>
            <option value="CLOSED">Cerrado</option>
          </select>

          <select v-model="mineFilters.priority" @change="loadMine">
            <option value="">Prioridad (todas)</option>
            <option value="LOW">Baja</option>
            <option value="MEDIUM">Media</option>
            <option value="HIGH">Alta</option>
          </select>
        </div>
      </div>

      <div v-if="loadingMine" class="muted">Cargando...</div>

      <div v-else class="list">
        <button
          v-for="c in mineCases"
          :key="c.id"
          class="row"
          @click="openCase(c.id)"
        >
          <div class="rowTop">
            <div class="title">{{ c.title }}</div>
            <span class="badge">{{ formatStatus(c.status) }}</span>
          </div>
          <div class="rowBottom">
            <span class="meta">Estudiante: <b>{{ c.student_id }}</b></span>
            <span class="meta">Prioridad: <b>{{ formatPriority(c.priority) }}</b></span>
            <span class="meta">Área: <b>{{ c.owner_area }}</b></span>
          </div>
        </button>

        <div v-if="!mineCases.length" class="muted">Sin casos por ahora.</div>
      </div>

      <p v-if="errorMine" class="err">{{ errorMine }}</p>
    </section>

    <!-- ✅ COMPARTIDOS CONMIGO (solo profesionales) -->
    <section v-else-if="tab==='shared'" class="card">
      <div class="cardHead">
        <div>
          <h2>Compartidos conmigo</h2>
          <p class="muted">Casos de otras áreas que te dieron acceso explícito (por usuario o por área).</p>
        </div>

        <div class="filters">
          <select v-model="sharedFilters.status" @change="loadShared">
            <option value="">Estado (todos)</option>
            <option value="OPEN">Abierto</option>
            <option value="IN_PROGRESS">En atención</option>
            <option value="RESOLVED">Resuelto</option>
            <option value="CLOSED">Cerrado</option>
          </select>

          <select v-model="sharedFilters.priority" @change="loadShared">
            <option value="">Prioridad (todas)</option>
            <option value="LOW">Baja</option>
            <option value="MEDIUM">Media</option>
            <option value="HIGH">Alta</option>
          </select>
        </div>
      </div>

      <div v-if="loadingShared" class="muted">Cargando...</div>

      <div v-else class="list">
        <button v-for="c in sharedCases" :key="c.id" class="row" @click="openCase(c.id)">
          <div class="rowTop">
            <div class="title">{{ c.title }}</div>
            <div class="badges">
              <span class="badge alt">Compartido</span>
              <span class="badge">{{ formatStatus(c.status) }}</span>
            </div>
          </div>
          <div class="rowBottom">
            <span class="meta">Estudiante: <b>{{ c.student_id }}</b></span>
            <span class="meta">Prioridad: <b>{{ formatPriority(c.priority) }}</b></span>
            <span class="meta">Área origen: <b>{{ c.owner_area }}</b></span>
          </div>
        </button>

        <div v-if="!sharedCases.length" class="muted">No tienes casos compartidos por ahora.</div>
      </div>

      <p v-if="errorShared" class="err">{{ errorShared }}</p>
    </section>

    <!-- ✅ BUSCAR POR ESTUDIANTE -->
    <section v-else class="card">
      <div class="cardHead">
        <h2>Casos por estudiante</h2>
        <p class="muted">Ingresa el identificador del estudiante para listar sus casos.</p>
      </div>

      <div class="fieldRow">
        <div class="field">
          <label>Student ID</label>
          <input v-model.trim="studentId" placeholder="Ej: 2024-00123 / CI / código interno" />
        </div>
        <button class="btn primary" :disabled="!studentId || loadingStudent" @click="searchStudent">
          {{ loadingStudent ? 'Buscando...' : 'Buscar' }}
        </button>
      </div>

      <div v-if="studentCases.length" class="list">
        <button
          v-for="c in studentCases"
          :key="c.id"
          class="row"
          @click="openCase(c.id)"
        >
          <div class="rowTop">
            <div class="title">{{ c.title }}</div>
            <span class="badge">{{ formatStatus(c.status) }}</span>
          </div>
          <div class="rowBottom">
            <span class="meta">Prioridad: <b>{{ formatPriority(c.priority) }}</b></span>
            <span class="meta">Área: <b>{{ c.owner_area }}</b></span>
          </div>
        </button>
      </div>

      <div v-else-if="searched && !loadingStudent" class="muted">No hay casos para este estudiante.</div>

      <p v-if="errorStudent" class="err">{{ errorStudent }}</p>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { listCases, listCasesByStudent } from '../../services/casesApi'
import { auth } from '../../stores/auth'
import { formatPriority, formatStatus } from '../../utils/caseFormatters'

const router = useRouter()

const role = computed(() => String(auth.user()?.role || '').toLowerCase())
const isProfessional = computed(() => role.value === 'professional')
const userId = computed(() => auth.user()?.id || auth.user()?.user_id || auth.user()?.sub || '')
const userArea = computed(() => auth.user()?.area || '')

const tab = ref('mine')

const mineCases = ref([])
const loadingMine = ref(false)
const errorMine = ref('')
const mineFilters = ref({ status: '', priority: '' })

const studentId = ref('')
const studentCases = ref([])
const loadingStudent = ref(false)
const errorStudent = ref('')
const searched = ref(false)

// Compartidos conmigo
const sharedCases = ref([])
const loadingShared = ref(false)
const errorShared = ref('')
const sharedFilters = ref({ status: '', priority: '' })

function openCase(id) {
  router.push(`/cases/${id}`)
}

async function loadMine() {
  loadingMine.value = true
  errorMine.value = ''
  try {
    const res = await listCases({ mine: true, status: mineFilters.value.status || undefined, priority: mineFilters.value.priority || undefined })
    mineCases.value = res?.items ?? res ?? []
  } catch (e) {
    errorMine.value = e?.message || 'No se pudieron cargar tus casos.'
  } finally {
    loadingMine.value = false
  }
}

async function searchStudent() {
  if (!studentId.value) return
  loadingStudent.value = true
  errorStudent.value = ''
  searched.value = true
  try {
    const res = await listCasesByStudent(studentId.value)
    studentCases.value = res?.items ?? res ?? []
  } catch (e) {
    errorStudent.value = e?.message || 'No se pudieron cargar los casos del estudiante.'
    studentCases.value = []
  } finally {
    loadingStudent.value = false
  }
}

function deriveShared(c) {
  // "Compartidos conmigo" = accesible, pero no es mío (creado/asignado) y no pertenece a mi área.
  const uid = String(userId.value || '')
  const area = String(userArea.value || '')
  const createdBy = String(c?.created_by_user_id || '')
  const assigned = String(c?.assigned_professional_id || '')
  const ownerArea = String(c?.owner_area || '')
  if (createdBy && createdBy === uid) return false
  if (assigned && assigned === uid) return false
  if (area && ownerArea && ownerArea === area) return false
  return true
}

async function loadShared() {
  if (!isProfessional.value) return
  loadingShared.value = true
  errorShared.value = ''
  try {
    // No existe un query param "shared_with_me" en el backend MVP.
    // Listamos todo lo accesible y filtramos por heurística (no mío y no de mi área).
    const res = await listCases({ status: sharedFilters.value.status || undefined, priority: sharedFilters.value.priority || undefined })
    const all = res?.items ?? res ?? []
    sharedCases.value = all.filter(deriveShared)
  } catch (e) {
    errorShared.value = e?.message || 'No se pudieron cargar los casos compartidos.'
  } finally {
    loadingShared.value = false
  }
}

function openShared() {
  tab.value = 'shared'
  if (!sharedCases.value.length) loadShared()
}

async function refresh() {
  if (tab.value === 'mine') return loadMine()
  if (tab.value === 'shared') return loadShared()
  if (tab.value === 'student' && studentId.value) return searchStudent()
}

onMounted(loadMine)
</script>

<style scoped>
.page{
  /* el ancho y padding lo maneja el layout global (App.vue + app.css) */
  padding: 0;
}
.head{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:16px;
  margin-bottom: 14px;
}
.actions{
  display:flex;
  gap:10px;
  align-items:center;
}
h1{ margin:0; font-size: 26px; }
.muted{ color:#6b7280; margin-top:4px; }
.err{ color:#b91c1c; margin-top:12px; }

.tabs{
  display:flex;
  gap:8px;
  margin: 14px 0 16px;
}
.tab{
  border: 1px solid #e5e7eb;
  background:#fff;
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 700;
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
  gap:16px;
  margin-bottom: 12px;
}
.cardHead h2{ margin:0; font-size:18px; }
.filters{ display:flex; gap:10px; }
.filters select{
  border:1px solid #e5e7eb;
  border-radius: 12px;
  padding: 8px 10px;
  background:#fff;
}

.fieldRow{
  display:flex;
  gap: 10px;
  align-items:flex-end;
  margin-bottom: 12px;
}
.field{ flex:1; display:flex; flex-direction:column; gap:6px; }
label{ font-size: 12px; color:#6b7280; }
input{
  border:1px solid #e5e7eb;
  border-radius: 12px;
  padding: 10px 12px;
  outline:none;
}

.list{ display:flex; flex-direction:column; gap:10px; }
.row{
  width:100%;
  text-align:left;
  border:1px solid #e5e7eb;
  border-radius: 14px;
  padding: 12px;
  background:#fff;
  cursor:pointer;
}
.row:hover{ background:#f9fafb; }
.rowTop{ display:flex; align-items:center; justify-content:space-between; gap:10px; }
.badges{ display:flex; align-items:center; gap:8px; }
.title{ font-weight: 800; color:#111827; }
.badge{
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  color:#374151;
}
.badge.alt{
  background:#eff6ff;
  border-color:#bfdbfe;
  color:#2563eb;
}
.rowBottom{
  display:flex;
  flex-wrap:wrap;
  gap: 12px;
  margin-top: 8px;
  color:#6b7280;
  font-size: 13px;
}
.meta b{ color:#111827; }

.btn{
  border:1px solid #e5e7eb;
  background:#fff;
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 700;
  cursor:pointer;
  color:#111827;
  text-decoration:none;
  display:inline-flex;
  align-items:center;
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
  .actions{ justify-content:flex-start; }
  .fieldRow{ flex-direction:column; align-items:stretch; }
  .filters{ flex-wrap:wrap; }
}
</style>
