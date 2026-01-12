<template>
  <section class="card">
    <header class="head">
      <div>
        <h1>Siniestros <small v-if="total" class="muted">({{ total }})</small></h1>
        <p class="muted">Listado con filtros (cacheado en Redis)</p>
      </div>
      <RouterLink class="btn" to="/insurance/claims/new">+ Nuevo</RouterLink>
    </header>

    <!-- Tabs: Draft vs Sent vs Approved vs History -->
    <div class="tabs">
      <button class="tab" :class="{active: tab==='draft'}" @click="setTab('draft')">Borradores</button>
      <button class="tab" :class="{active: tab==='sent'}" @click="setTab('sent')">Enviados</button>
      <button class="tab" :class="{active: tab==='approved'}" @click="setTab('approved')">Aprobados</button>
      <button class="tab" :class="{active: tab==='history'}" @click="setTab('history')">Historial</button>
    </div>

    <div class="filters">
      <input v-model.trim="filters.student_id" placeholder="Student ID (cédula/código)" />
      <!-- Status is primarily controlled by the tab; extra filter remains available if you want "all" -->
      <select v-model="filters.status">
        <option value="">Estado (según pestaña)</option>
        <option value="DRAFT">DRAFT</option>
        <option value="SUBMITTED">SUBMITTED</option>
        <option value="UNDER_REVIEW">UNDER_REVIEW</option>
        <option value="APPROVED">APPROVED</option>
        <option value="REJECTED">REJECTED</option>
        <option value="CLOSED">CLOSED</option>
      </select>

      <select v-model="filters.type">
        <option value="">Tipo (todos)</option>
        <option value="ACCIDENT">ACCIDENT</option>
        <option value="ILLNESS">ILLNESS</option>
        <option value="FAMILY_DEATH">FAMILY_DEATH</option>
        <option value="OTHER">OTHER</option>
      </select>

      <button class="ghost" @click="load" :disabled="loading">Buscar</button>
    </div>

    <p v-if="loading"><small class="muted">Cargando...</small></p>
    <p v-if="error" class="err">{{ error }}</p>

    <div v-if="items?.length" class="tableWrap">
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Student</th>
            <th>Type</th>
            <th>Status</th>
            <th>Requested</th>
            <th>Cap</th>
            <th>Approved</th>
            <th>Payment</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in items" :key="c.id" @click="go(c.id)" class="row">
            <td class="mono">{{ short(c.id) }}</td>
            <td>{{ c.student_id }}</td>
            <td>{{ c.claim_type }}</td>
            <td><span class="pill">{{ c.status }}</span></td>
            <td>$ {{ c.requested_amount }}</td>
            <td>$ {{ c.coverage_cap }}</td>
            <td>{{ c.approved_amount == null ? '-' : ('$ '+c.approved_amount) }}</td>
            <td>{{ c.payment_status }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else-if="!loading" class="muted">No hay resultados en esta pestaña.</p>
  </section>
</template>

<script setup>
import { reactive, ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { listClaims } from '../../services/claimsApi'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const error = ref('')
const items = ref([])
const total = ref(0)

const tab = computed(() => String(route.query.tab || 'draft'))

const filters = reactive({
  status: '',
  type: '',
  student_id: ''
})

function short(id){ return String(id).slice(0,8)+'…' }
function go(id){ router.push(`/insurance/claims/${id}`) }

async function load(){
  loading.value = true
  error.value = ''
  try{
    const base = {}
    if(filters.type) base.type = filters.type
    if(filters.student_id) base.student_id = filters.student_id

    // If user explicitly picks a status, use it. Otherwise, use the tab defaults.
    const explicitStatus = filters.status || null
    if(explicitStatus){
      items.value = await listClaims({ ...base, status: explicitStatus })
    } else if(tab.value === 'draft') {
      items.value = await listClaims({ ...base, status:'DRAFT' })
    } else if(tab.value === 'sent') {
      const [a,b] = await Promise.all([
        listClaims({ ...base, status:'SUBMITTED' }),
        listClaims({ ...base, status:'UNDER_REVIEW' })
      ])
      items.value = [...a, ...b]
    } else if(tab.value === 'approved') {
      items.value = await listClaims({ ...base, status:'APPROVED' })
    } else {
      const [c1,c2] = await Promise.all([
        listClaims({ ...base, status:'CLOSED' }),
        listClaims({ ...base, status:'REJECTED' })
      ])
      items.value = [...c1, ...c2]
    }

    // Sort by created_at desc for better UX
    items.value = Array.isArray(items.value)
      ? [...items.value].sort((x,y)=> String(y.created_at).localeCompare(String(x.created_at)))
      : []
    total.value = Array.isArray(items.value) ? items.value.length : 0
  }catch(e){
    error.value = String(e?.message || e)
  }finally{
    loading.value = false
  }
}

function setTab(t){
  // Reset explicit status filter to keep tabs intuitive
  filters.status = ''
  router.push({ path:'/insurance/claims', query:{ tab: t } })
}

onMounted(load)
watch(() => route.query.tab, () => { load() })
</script>

<style scoped>
.card{ background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:16px; }
.head{ display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:12px; }
h1{ margin:0;font-size:20px; }
.filters{ display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:12px; }
.tabs{ display:flex; gap:8px; margin: 6px 0 12px; flex-wrap:wrap; }
.tab{ background:#f3f4f6;border:1px solid #e5e7eb;border-radius:999px;padding:8px 12px; cursor:pointer; font-size:13px; }
.tab.active{ background:#111827; color:#fff; border-color:#111827; }
input, select{
  border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px;outline:none;
}
.btn{
  text-decoration:none;
  background:#2563eb;color:#fff;padding:10px 12px;border-radius:12px;
}
.ghost{
  background:#f3f4f6;border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px;cursor:pointer;
}
.tableWrap{ overflow:auto;border:1px solid #eef2f7;border-radius:14px; }
.table{ width:100%;border-collapse:collapse;font-size:13px; }
th, td{ padding:10px 12px;border-bottom:1px solid #eef2f7; text-align:left; }
.row{ cursor:pointer; }
.row:hover{ background:#fafafa; }
.pill{ display:inline-block;padding:4px 8px;border-radius:999px;background:#eff6ff;border:1px solid #dbeafe;font-size:12px; }
.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.err{ color:#b91c1c; }
.muted{ color:#6b7280; }

@media (max-width: 768px){
  /* Evita recortes horizontales por headers/inputs muy anchos */
  .head{
    flex-direction: column;
    align-items: stretch;
  }
  .btn{
    width: 100%;
    text-align: center;
  }
  .filters > input,
  .filters > select,
  .filters > button{
    flex: 1 1 160px;
    min-width: 0;
    width: 100%;
  }
  .tableWrap{
    /* asegura scroll horizontal si hace falta, sin cortar */
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .table{
    min-width: 720px; /* fuerza scroll horizontal en pantallas pequeñas */
  }
}
</style>
