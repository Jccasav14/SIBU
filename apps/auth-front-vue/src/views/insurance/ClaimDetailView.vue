<template>
  <div class="stack">
    <section class="card">
      <header class="head">
        <div>
          <h1>Siniestro {{ short(id) }}</h1>
          <p class="muted">Detalle + acciones por estado</p>
        </div>
        <div class="headActions">
          <RouterLink class="ghost" to="/insurance/claims">Volver</RouterLink>
          <button class="ghost" @click="load" :disabled="loading">Actualizar</button>
        </div>
      </header>

      <p v-if="loading"><small class="muted">Cargando...</small></p>
      <p v-if="error" class="err">{{ error }}</p>

      <div v-if="claim" class="grid">
        <div class="kv"><span class="k">Student</span><span class="v">{{ claim.student_id }}</span></div>
        <div class="kv"><span class="k">Type</span><span class="v">{{ claim.claim_type }}</span></div>
        <div class="kv"><span class="k">Status</span><span class="v"><span class="pill">{{ claim.status }}</span></span></div>
        <div class="kv"><span class="k">Payment</span><span class="v">{{ claim.payment_status }}</span></div>

        <div class="kv"><span class="k">Requested</span><span class="v">$ {{ claim.requested_amount }}</span></div>
        <div class="kv"><span class="k">Coverage cap</span><span class="v">$ {{ claim.coverage_cap }}</span></div>
        <div class="kv"><span class="k">Approved</span><span class="v">{{ claim.approved_amount==null?'-':'$ '+claim.approved_amount }}</span></div>
        <div class="kv"><span class="k">Paid</span><span class="v">{{ claim.paid_amount==null?'-':'$ '+claim.paid_amount }}</span></div>

        <div class="kv full">
          <span class="k">Description</span>
          <span class="v">{{ claim.description }}</span>
        </div>
      </div>

      <div v-if="claim" class="actions">
        <!-- Edit only in DRAFT -->
        <div v-if="claim.status==='DRAFT'" class="actionCard">
          <h3>Editar (solo DRAFT)</h3>
          <form class="row" @submit.prevent="doPatch">
            <input v-model.number="edit.requested_amount" type="number" min="0" step="0.01" placeholder="Requested" />
            <input v-model.number="edit.coverage_cap" type="number" min="0" step="0.01" placeholder="Cap" />
            <button class="ghost" :disabled="busy">Guardar</button>
          </form>
          <textarea v-model="edit.description" rows="3" placeholder="Update description..."></textarea>
        </div>

        <div v-if="claim.status==='DRAFT'" class="actionCard">
          <h3>Enviar</h3>
          <p class="muted">DRAFT → SUBMITTED</p>
          <button class="btn" @click="doSubmit" :disabled="busy">Enviar siniestro</button>
        </div>

        <div v-if="claim.status==='SUBMITTED' || claim.status==='UNDER_REVIEW'" class="actionCard">
          <h3>Revisión</h3>
          <p class="muted">Aprobar o rechazar</p>

          <div class="row">
            <select v-model="review.decision">
              <option value="APPROVE">Aprobar</option>
              <option value="REJECT">Rechazar</option>
            </select>
            <input
              v-if="review.decision==='APPROVE'"
              v-model.number="review.approved_amount"
              type="number"
              min="0"
              step="0.01"
              placeholder="Monto aprobado"
            />
          </div>
          <textarea v-model="review.notes" rows="2" placeholder="Notas (opcional)"></textarea>

          <button class="btn" @click="doReview" :disabled="busy">Confirmar revisión</button>
        </div>

        <div v-if="claim.status==='APPROVED'" class="actionCard">
          <h3>Pago</h3>
          <p class="muted">APPROVED → PAID/CLOSED</p>

          <div class="row">
            <input v-model="payment.payment_method" placeholder="Method e.g. BANK_TRANSFER" />
            <input v-model="payment.payment_reference" placeholder="Reference" />
            <input v-model.number="payment.paid_amount" type="number" min="0" step="0.01" placeholder="Paid amount" />
          </div>

          <button class="btn" @click="doPay" :disabled="busy">Registrar pago</button>
        </div>
      </div>

      <p v-if="ok" class="ok">{{ ok }}</p>
      <p v-if="err" class="err">{{ err }}</p>
    </section>

    <section class="card">
      <header class="head">
        <div>
          <h2>Documentos</h2>
          <p class="muted">Adjunta evidencias (solo URL/path + hash)</p>
        </div>
        <button class="ghost" @click="loadDocs" :disabled="busy">Actualizar</button>
      </header>

      <form class="docForm" @submit.prevent="addDoc">
        <select v-model="doc.doc_type" required>
          <option value="invoice">invoice</option>
          <option value="medical_report">medical_report</option>
          <option value="death_certificate">death_certificate</option>
          <option value="other">other</option>
        </select>
        <input v-model.trim="doc.file_url" required placeholder="file_url (no upload)"/>
        <input v-model.trim="doc.file_hash" required placeholder="file_hash"/>
        <button class="ghost" :disabled="busy">Agregar</button>
      </form>

      <div v-if="docs?.length" class="tableWrap">
        <table class="table">
          <thead><tr><th>Type</th><th>URL</th><th>Hash</th><th>At</th></tr></thead>
          <tbody>
            <tr v-for="d in docs" :key="d.id">
              <td>{{ d.doc_type }}</td>
              <td class="mono">{{ d.file_url }}</td>
              <td class="mono">{{ d.file_hash }}</td>
              <td>{{ format(d.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="muted">Sin documentos todavía.</p>
    </section>

    <section class="card">
      <header class="head">
        <div>
          <h2>Timeline</h2>
          <p class="muted">Eventos del siniestro</p>
        </div>
        <button class="ghost" @click="loadTimeline" :disabled="busy">Actualizar</button>
      </header>

      <div v-if="timeline?.length" class="timeline">
        <div class="ev" v-for="e in timeline" :key="e.id">
          <div class="evTop">
            <span class="pill">{{ e.event_type }}</span>
            <span class="muted">{{ e.actor }}</span>
            <span class="muted">{{ format(e.created_at) }}</span>
          </div>
          <pre class="payload">{{ pretty(e.payload_json) }}</pre>
        </div>
      </div>
      <p v-else class="muted">Sin eventos todavía.</p>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getClaim, patchClaim, submitClaim, reviewClaim, payClaim, getDocuments, addDocument, getTimeline } from '../../services/claimsApi'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id)

const loading = ref(false)
const busy = ref(false)
const error = ref('')
const ok = ref('')
const err = ref('')
const claim = ref(null)

const edit = reactive({ description:'', requested_amount:0, coverage_cap:0 })
const review = reactive({ decision:'APPROVE', approved_amount:0, notes:'' })
const payment = reactive({ payment_method:'BANK_TRANSFER', payment_reference:'', paid_amount:0 })
const doc = reactive({ doc_type:'medical_report', file_url:'', file_hash:'' })

const docs = ref([])
const timeline = ref([])

function short(x){ return String(x||'').slice(0,8)+'…' }
function format(ts){ try{ return new Date(ts).toLocaleString() }catch{ return ts } }
function pretty(x){ try{ return JSON.stringify(x, null, 2) }catch{ return String(x) } }

function syncForm(){
  edit.description = claim.value?.description || ''
  edit.requested_amount = claim.value?.requested_amount || 0
  edit.coverage_cap = claim.value?.coverage_cap || 0
  review.approved_amount = claim.value?.approved_amount ?? claim.value?.requested_amount ?? 0
  payment.paid_amount = claim.value?.approved_amount ?? claim.value?.requested_amount ?? 0
}

async function load(){
  loading.value = true
  error.value = ''
  ok.value = ''
  err.value = ''
  try{
    claim.value = await getClaim(id.value)
    syncForm()
  }catch(e){
    error.value = String(e?.message || e)
  }finally{
    loading.value = false
  }
}

async function loadDocs(){
  try{ docs.value = await getDocuments(id.value) }catch(e){ /* ignore */ }
}
async function loadTimeline(){
  try{ timeline.value = await getTimeline(id.value) }catch(e){ /* ignore */ }
}

async function doPatch(){
  busy.value = true
  err.value = ''
  ok.value = ''
  try{
    await patchClaim(id.value, {
      description: edit.description,
      requested_amount: edit.requested_amount,
      coverage_cap: edit.coverage_cap
    })
    ok.value = 'Actualizado.'
    await load()
  }catch(e){
    err.value = String(e?.message || e)
  }finally{
    busy.value = false
  }
}

async function doSubmit(){
  busy.value = true
  err.value = ''
  ok.value = ''
  try{
    await submitClaim(id.value)
    ok.value = 'Enviado.'
    await load()
    await loadTimeline()
    // After submitting, return to the "Sent" list for continuity
    try{ await router.push({ path:'/insurance/claims', query:{ tab:'sent' } }) }catch{}
  }catch(e){
    err.value = String(e?.message || e)
  }finally{
    busy.value = false
  }
}

async function doReview(){
  busy.value = true
  err.value = ''
  ok.value = ''
  try{
    const payload = { decision: review.decision, notes: review.notes }
    if(review.decision === 'APPROVE') payload.approved_amount = review.approved_amount
    await reviewClaim(id.value, payload)
    ok.value = 'Revisión registrada.'
    await load()
    await loadTimeline()
  }catch(e){
    err.value = String(e?.message || e)
  }finally{
    busy.value = false
  }
}

async function doPay(){
  busy.value = true
  err.value = ''
  ok.value = ''
  try{
    await payClaim(id.value, payment)
    ok.value = 'Pago registrado.'
    await load()
    await loadTimeline()
  }catch(e){
    err.value = String(e?.message || e)
  }finally{
    busy.value = false
  }
}

async function addDoc(){
  busy.value = true
  err.value = ''
  ok.value = ''
  try{
    await addDocument(id.value, doc)
    ok.value = 'Documento agregado.'
    doc.file_url = ''
    doc.file_hash = ''
    await loadDocs()
    await loadTimeline()
  }catch(e){
    err.value = String(e?.message || e)
  }finally{
    busy.value = false
  }
}

onMounted(async () => {
  await load()
  await loadDocs()
  await loadTimeline()
})
</script>

<style scoped>
.stack{ display:flex; flex-direction:column; gap: 14px; }
.card{ background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:16px; }
.head{ display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:12px; }
.headActions{ display:flex; gap: 8px; }
h1{ margin:0;font-size:20px; }
h2{ margin:0;font-size:16px; }
.grid{ display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 10px; }
.kv{ display:flex; flex-direction:column; gap: 4px; border:1px solid #eef2f7; border-radius: 14px; padding: 10px; background:#fafafa; }
.k{ font-size:12px; color:#6b7280; }
.v{ font-weight:700; }
.full{ grid-column: 1 / -1; }
.actions{ display:grid; grid-template-columns: repeat(auto-fit, minmax(260px,1fr)); gap: 12px; margin-top: 12px; }
.actionCard{ border:1px solid #eef2f7; border-radius:14px; padding: 12px; background:#fff; display:flex; flex-direction:column; gap: 10px; }
.row{ display:flex; gap: 10px; flex-wrap:wrap; align-items:center; }
input, select, textarea{
  border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px;outline:none;
}
.btn{ background:#2563eb;color:#fff;border:none;padding:10px 12px;border-radius:12px;cursor:pointer; }
.ghost{ text-decoration:none;background:#f3f4f6;border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px;color:#111827; cursor:pointer; }
.pill{ display:inline-block;padding:4px 8px;border-radius:999px;background:#eff6ff;border:1px solid #dbeafe;font-size:12px; }
.tableWrap{ overflow:auto;border:1px solid #eef2f7;border-radius:14px; }
.table{ width:100%;border-collapse:collapse;font-size:13px; }
th, td{ padding:10px 12px;border-bottom:1px solid #eef2f7; text-align:left; }
.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.timeline{ display:flex; flex-direction:column; gap: 10px; }
.ev{ border:1px solid #eef2f7;border-radius:14px; padding: 10px; background:#fafafa; }
.evTop{ display:flex; gap: 8px; align-items:center; flex-wrap:wrap; margin-bottom: 8px; }
.payload{ margin:0; white-space: pre-wrap; font-size:12px; }
.err{ color:#b91c1c; }
.ok{ color:#047857; }
.muted{ color:#6b7280; }
</style>
