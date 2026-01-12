<template>
  <section class="card">
    <header class="head">
      <div>
        <h1>Coberturas y Políticas</h1>
        <p class="muted">Reglas de cobertura usadas por el módulo de siniestros.</p>
      </div>
      <div class="actions">
        <select class="select" v-model="claimTypeFilter">
          <option value="">Todas</option>
          <option v-for="t in claimTypes" :key="t" :value="t">{{ labelClaimType(t) }}</option>
        </select>
        <button class="btn" @click="load" :disabled="loading">Actualizar</button>
        <button v-if="isAdmin" class="btn secondary" @click="startCreate">Nueva</button>
      </div>
    </header>

    <p v-if="loading"><small class="muted">Cargando...</small></p>
    <p v-if="error" class="err">{{ error }}</p>

    <div v-if="rows.length" class="tableWrap">
      <table class="table">
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Nombre</th>
            <th>Máximo</th>
            <th>Espera (días)</th>
            <th>Vigencia</th>
            <th>Activa</th>
            <th class="right">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in rows" :key="p.id">
            <td><span class="pill">{{ labelClaimType(p.claim_type) }}</span></td>
            <td>
              <div class="name">{{ p.name }}</div>
              <div class="desc" v-if="p.description">{{ p.description }}</div>
            </td>
            <td class="mono">{{ formatMoney(p.max_coverage_amount, p.currency) }}</td>
            <td class="mono">{{ p.waiting_days }}</td>
            <td class="mono">{{ fmtDate(p.valid_from) }} → {{ p.valid_to ? fmtDate(p.valid_to) : '—' }}</td>
            <td>
              <span :class="['status', p.is_active ? 'on' : 'off']">
                {{ p.is_active ? 'Sí' : 'No' }}
              </span>
            </td>
            <td class="right">
              <button class="linkBtn" @click="openDetails(p)">Ver</button>
              <template v-if="isAdmin">
                <button class="linkBtn" @click="startEdit(p)">Editar</button>
                <button v-if="!p.is_active" class="linkBtn" @click="onActivate(p)">Activar</button>
                <button v-else class="linkBtn danger" @click="onDeactivate(p)">Desactivar</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else-if="!loading" class="muted"><small>No hay políticas registradas.</small></p>

    <!-- Drawer: details + upsert -->
    <div v-if="panelOpen" class="backdrop" @click.self="closePanel">
      <div class="panel">
        <header class="panelHead">
          <div>
            <div class="panelTitle">
              {{ mode === 'view' ? 'Detalle' : mode === 'create' ? 'Nueva cobertura' : 'Editar cobertura' }}
            </div>
            <div class="panelSub" v-if="activePolicy?.id"><small class="muted">ID: {{ activePolicy.id }}</small></div>
          </div>
          <button class="x" @click="closePanel">✕</button>
        </header>

        <div v-if="mode === 'view'" class="panelBody">
          <div class="kv"><span>Tipo</span><b>{{ labelClaimType(activePolicy.claim_type) }}</b></div>
          <div class="kv"><span>Nombre</span><b>{{ activePolicy.name }}</b></div>
          <div class="kv" v-if="activePolicy.description"><span>Descripción</span><b>{{ activePolicy.description }}</b></div>
          <div class="kv"><span>Máximo</span><b>{{ formatMoney(activePolicy.max_coverage_amount, activePolicy.currency) }}</b></div>
          <div class="kv"><span>Espera</span><b>{{ activePolicy.waiting_days }} días</b></div>
          <div class="kv"><span>Documentos</span><b>{{ docsLabel(activePolicy.requires_documents) }}</b></div>
          <div class="kv"><span>Vigencia</span><b>{{ fmtDate(activePolicy.valid_from) }} → {{ activePolicy.valid_to ? fmtDate(activePolicy.valid_to) : '—' }}</b></div>
          <div class="kv"><span>Activa</span><b>{{ activePolicy.is_active ? 'Sí' : 'No' }}</b></div>

          <div v-if="isAdmin" class="panelActions">
            <button class="btn secondary" @click="startEdit(activePolicy)">Editar</button>
            <button v-if="!activePolicy.is_active" class="btn" @click="onActivate(activePolicy)">Activar</button>
            <button v-else class="btn danger" @click="onDeactivate(activePolicy)">Desactivar</button>
          </div>
        </div>

        <form v-else class="panelBody" @submit.prevent="save">
          <div class="grid">
            <div class="row">
              <label>Tipo de reclamo</label>
              <select v-model="form.claim_type" required>
                <option v-for="t in claimTypes" :key="t" :value="t">{{ labelClaimType(t) }}</option>
              </select>
            </div>
            <div class="row">
              <label>Nombre</label>
              <input v-model.trim="form.name" required />
            </div>
          </div>

          <div class="row">
            <label>Descripción</label>
            <textarea v-model.trim="form.description" rows="3" />
          </div>

          <div class="grid">
            <div class="row">
              <label>Monto máximo</label>
              <input v-model.number="form.max_coverage_amount" type="number" min="0" step="0.01" required />
            </div>
            <div class="row">
              <label>Moneda</label>
              <input v-model.trim="form.currency" placeholder="USD" />
            </div>
          </div>

          <div class="grid">
            <div class="row">
              <label>Días de espera</label>
              <input v-model.number="form.waiting_days" type="number" min="0" step="1" required />
            </div>
            <div class="row">
              <label>Activa</label>
              <select v-model="form.is_active">
                <option :value="true">Sí</option>
                <option :value="false">No</option>
              </select>
            </div>
          </div>

          <div class="row">
            <label>Documentos requeridos (separados por coma)</label>
            <input v-model.trim="form.requires_documents" placeholder="medical_report, invoice" />
          </div>

          <div class="grid">
            <div class="row">
              <label>Válida desde</label>
              <input v-model="form.valid_from" type="date" required />
            </div>
            <div class="row">
              <label>Válida hasta (opcional)</label>
              <input v-model="form.valid_to" type="date" />
            </div>
          </div>

          <p v-if="saveError" class="err">{{ saveError }}</p>

          <div class="panelActions">
            <button class="btn" type="submit" :disabled="saving">Guardar</button>
            <button class="btn secondary" type="button" @click="closePanel">Cancelar</button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { auth } from '../../stores/auth'
import {
  activateCoverage,
  createCoverage,
  deactivateCoverage,
  listCoverages,
  patchCoverage
} from '../../services/coverageApi'

const router = useRouter()
const route = useRoute()

const role = computed(() => String(auth.user()?.role || '').toLowerCase())
const isAdmin = computed(() => role.value === 'admin')

const claimTypes = ['ACCIDENT', 'ILLNESS', 'FAMILY_DEATH', 'OTHER']
const claimTypeFilter = ref('')

const loading = ref(false)
const error = ref('')
const rows = ref([])

const panelOpen = ref(false)
const mode = ref('view') // view | create | edit
const activePolicy = ref(null)

const saving = ref(false)
const saveError = ref('')
const form = ref({
  claim_type: 'ACCIDENT',
  name: '',
  description: '',
  max_coverage_amount: 0,
  currency: 'USD',
  requires_documents: '',
  waiting_days: 0,
  is_active: true,
  valid_from: '',
  valid_to: ''
})

function labelClaimType(t){
  const v = String(t || '').toUpperCase()
  if(v === 'ACCIDENT') return 'Accidente'
  if(v === 'ILLNESS') return 'Enfermedad'
  if(v === 'FAMILY_DEATH') return 'Fallecimiento familiar'
  return 'Otro'
}

function fmtDate(s){
  if(!s) return '—'
  return String(s).slice(0, 10)
}

function formatMoney(amount, currency){
  const c = currency || 'USD'
  const n = Number(amount || 0)
  return `${c} ${n.toFixed(2)}`
}

function docsLabel(v){
  if(!v) return '—'
  if(Array.isArray(v)) return v.length ? v.join(', ') : '—'
  if(typeof v === 'string') return v.trim() ? v : '—'
  return '—'
}

async function load(){
  loading.value = true
  error.value = ''
  try{
    const all = await listCoverages()
    const f = claimTypeFilter.value
    rows.value = f ? all.filter((x) => String(x.claim_type || '').toUpperCase() === f) : all
  }catch(e){
    error.value = String(e?.message || e)
  }finally{
    loading.value = false
  }
}

watch(claimTypeFilter, () => load())

function closePanel(){
  panelOpen.value = false
  mode.value = 'view'
  activePolicy.value = null
  saveError.value = ''
  // remove ?new=1 if present
  if(route.query?.new){
    router.replace({ query: { ...route.query, new: undefined } })
  }
}

function openDetails(p){
  activePolicy.value = p
  mode.value = 'view'
  panelOpen.value = true
}

function startCreate(){
  if(!isAdmin.value) return
  activePolicy.value = null
  mode.value = 'create'
  panelOpen.value = true
  const today = new Date().toISOString().slice(0,10)
  form.value = {
    claim_type: 'ACCIDENT',
    name: '',
    description: '',
    max_coverage_amount: 0,
    currency: 'USD',
    requires_documents: '',
    waiting_days: 0,
    is_active: true,
    valid_from: today,
    valid_to: ''
  }
}

function startEdit(p){
  if(!isAdmin.value) return
  activePolicy.value = p
  mode.value = 'edit'
  panelOpen.value = true
  form.value = {
    claim_type: String(p.claim_type || 'ACCIDENT').toUpperCase(),
    name: p.name || '',
    description: p.description || '',
    max_coverage_amount: Number(p.max_coverage_amount || 0),
    currency: p.currency || 'USD',
    requires_documents: Array.isArray(p.requires_documents) ? p.requires_documents.join(', ') : (p.requires_documents || ''),
    waiting_days: Number(p.waiting_days || 0),
    is_active: Boolean(p.is_active),
    valid_from: fmtDate(p.valid_from),
    valid_to: fmtDate(p.valid_to)
  }
}

function toPayload(){
  const docs = String(form.value.requires_documents || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  return {
    claim_type: String(form.value.claim_type || '').toUpperCase(),
    name: form.value.name,
    description: form.value.description || null,
    max_coverage_amount: Number(form.value.max_coverage_amount || 0),
    currency: (form.value.currency || 'USD').toUpperCase(),
    requires_documents: docs,
    waiting_days: Number(form.value.waiting_days || 0),
    is_active: Boolean(form.value.is_active),
    valid_from: form.value.valid_from,
    valid_to: form.value.valid_to || null
  }
}

async function save(){
  if(!isAdmin.value) return
  saving.value = true
  saveError.value = ''
  try{
    if(mode.value === 'create'){
      await createCoverage(toPayload())
    }else if(mode.value === 'edit' && activePolicy.value?.id){
      await patchCoverage(activePolicy.value.id, toPayload())
    }
    await load()
    closePanel()
  }catch(e){
    saveError.value = String(e?.message || e)
  }finally{
    saving.value = false
  }
}

async function onActivate(p){
  if(!isAdmin.value) return
  try{
    await activateCoverage(p.id)
    await load()
    if(panelOpen.value && activePolicy.value?.id === p.id){
      activePolicy.value = rows.value.find((x) => x.id === p.id) || activePolicy.value
    }
  }catch(e){
    error.value = String(e?.message || e)
  }
}

async function onDeactivate(p){
  if(!isAdmin.value) return
  try{
    await deactivateCoverage(p.id)
    await load()
    if(panelOpen.value && activePolicy.value?.id === p.id){
      activePolicy.value = rows.value.find((x) => x.id === p.id) || activePolicy.value
    }
  }catch(e){
    error.value = String(e?.message || e)
  }
}

onMounted(async () => {
  await load()
  if(route.query?.new && isAdmin.value){
    startCreate()
  }
})
</script>

<style scoped>
.card{
  background:#fff;
  border:1px solid #e5e7eb;
  border-radius:14px;
  padding: 16px;
}
.head{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  gap: 12px;
  margin-bottom: 12px;
}
h1{ margin:0; font-size: 20px; }
.muted{ color:#6b7280; }
.err{ color:#b91c1c; }
.actions{ display:flex; align-items:center; gap: 10px; flex-wrap: wrap; justify-content:flex-end; }
.select{
  border:1px solid #e5e7eb;
  border-radius: 12px;
  padding: 10px 12px;
  background:#fff;
}
.btn{
  background:#2563eb;
  color:#fff;
  border:none;
  padding: 10px 12px;
  border-radius: 12px;
  cursor:pointer;
}
.btn.secondary{
  background:#111827;
}
.btn.danger{ background:#b91c1c; }
.btn:disabled{ opacity:.6; cursor:not-allowed; }

.tableWrap{ overflow:auto; border:1px solid #eef2f7; border-radius: 14px; }
.table{ width:100%; border-collapse: collapse; min-width: 840px; }
.table th, .table td{ text-align:left; padding: 12px 12px; border-bottom: 1px solid #eef2f7; vertical-align: top; }
.table th{ font-size: 12px; color:#6b7280; text-transform: uppercase; letter-spacing: .04em; }
.right{ text-align:right; }
.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 12.5px; }
.pill{ display:inline-flex; padding: 4px 10px; border-radius: 999px; background:#eff6ff; border:1px solid #dbeafe; font-size: 12px; font-weight: 700; color:#1d4ed8; }
.name{ font-weight: 800; }
.desc{ font-size: 12px; color:#6b7280; margin-top: 4px; }
.status{ display:inline-flex; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 800; border: 1px solid transparent; }
.status.on{ background:#ecfdf5; color:#047857; border-color:#a7f3d0; }
.status.off{ background:#f3f4f6; color:#374151; border-color:#e5e7eb; }
.linkBtn{ background:transparent; border:none; cursor:pointer; color:#2563eb; font-weight: 800; padding: 6px 8px; border-radius: 10px; }
.linkBtn:hover{ background:#eff6ff; }
.linkBtn.danger{ color:#b91c1c; }
.linkBtn.danger:hover{ background:#fee2e2; }

.backdrop{
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.35);
  display:flex;
  align-items: stretch;
  justify-content: flex-end;
  z-index: 60;
}
.panel{
  width: min(520px, 92vw);
  background:#fff;
  height: 100%;
  padding: 14px;
  display:flex;
  flex-direction: column;
  box-shadow: -20px 0 60px rgba(0,0,0,0.25);
}
.panelHead{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap: 10px;
  border-bottom: 1px solid #eef2f7;
  padding-bottom: 10px;
}
.panelTitle{ font-weight: 900; font-size: 16px; }
.panelSub{ margin-top: 2px; }
.x{ border:none; background:#f3f4f6; border-radius: 12px; padding: 8px 10px; cursor:pointer; }
.panelBody{ padding-top: 12px; overflow:auto; }
.kv{ display:flex; justify-content:space-between; gap: 12px; padding: 10px 0; border-bottom: 1px dashed #eef2f7; }
.kv span{ color:#6b7280; }
.panelActions{ display:flex; gap: 10px; justify-content:flex-end; padding-top: 14px; }

form .row{ display:flex; flex-direction:column; gap: 6px; margin-bottom: 12px; }
form label{ font-weight: 800; font-size: 12px; color:#374151; }
form input, form select, form textarea{
  border:1px solid #e5e7eb;
  border-radius: 12px;
  padding: 10px 12px;
  font: inherit;
}
.grid{ display:grid; grid-template-columns: 1fr 1fr; gap: 10px; }
@media (max-width: 700px){
  .grid{ grid-template-columns: 1fr; }
}
</style>
