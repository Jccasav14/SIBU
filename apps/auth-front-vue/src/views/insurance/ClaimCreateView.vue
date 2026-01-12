<template>
  <section class="card">
    <header class="head">
      <div>
        <h1>Crear siniestro</h1>
        <p class="muted">Se crea en estado <b>DRAFT</b></p>
      </div>
      <RouterLink class="ghost" to="/insurance/claims">Volver</RouterLink>
    </header>

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="ok" class="ok">{{ ok }}</p>

    <form class="grid" @submit.prevent="submit">
      <div class="field">
        <label>Student ID</label>
        <input v-model.trim="form.student_id" required placeholder="cédula o código interno"/>
      </div>

      <div class="field">
        <label>Tipo</label>
        <select v-model="form.claim_type" required>
          <option value="ACCIDENT">ACCIDENT</option>
          <option value="ILLNESS">ILLNESS</option>
          <option value="FAMILY_DEATH">FAMILY_DEATH</option>
          <option value="OTHER">OTHER</option>
        </select>
      </div>

      <div class="field">
        <label>Ocurrió</label>
        <input v-model="form.occurred_at" type="datetime-local" required />
      </div>

      <div class="field">
        <label>Reportado</label>
        <input v-model="form.reported_at" type="datetime-local" required />
      </div>

      <div class="field full">
        <label>Descripción</label>
        <textarea v-model="form.description" rows="4" required placeholder="Describe el evento cubierto..."></textarea>
      </div>

      <div class="field">
        <label>Monto solicitado</label>
        <input v-model.number="form.requested_amount" type="number" min="0" step="0.01" required />
      </div>

      <div class="field">
        <label>Tope de cobertura</label>
        <input v-model.number="form.coverage_cap" type="number" min="0" step="0.01" readonly />
      </div>

      <div class="actions full">
        <button class="btn" :disabled="loading">
          {{ loading ? 'Creando...' : 'Crear siniestro' }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup>
import { reactive, ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createClaim } from '../../services/claimsApi'
import { listCoverageByClaimType } from '../../services/coverageApi'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const ok = ref('')

const form = reactive({
  student_id: '',
  claim_type: 'ACCIDENT',
  occurred_at: '',
  reported_at: '',
  description: '',
  requested_amount: 0,
  coverage_cap: 0
})

function toISO(local){
  // local datetime-local: YYYY-MM-DDTHH:mm
  if(!local) return null
  const d = new Date(local)
  return d.toISOString()
}

async function refreshCoverageCap(){
  try {
    const items = await listCoverageByClaimType(form.claim_type)
    const policy = Array.isArray(items) ? items.find(p => p && p.is_active) || items[0] : null
    form.coverage_cap = policy ? Number(policy.max_coverage_amount || 0) : 0

    if (Number(form.requested_amount) > Number(form.coverage_cap || 0)) {
      form.requested_amount = Number(form.coverage_cap || 0)
    }
  } catch (e) {
    // best-effort: if coverage is unreachable, keep current cap
    form.coverage_cap = Number(form.coverage_cap || 0)
  }
}

watch(() => form.claim_type, async () => {
  await refreshCoverageCap()
})

onMounted(async () => {
  await refreshCoverageCap()
})

watch(() => form.requested_amount, (v) => {
  const cap = Number(form.coverage_cap || 0)
  if (cap > 0 && Number(v) > cap) form.requested_amount = cap
  if (Number(form.requested_amount) < 0) form.requested_amount = 0
})


async function submit(){
  loading.value = true
  error.value = ''
  ok.value = ''
  try{
    const payload = {
      ...form,
      occurred_at: toISO(form.occurred_at),
      reported_at: toISO(form.reported_at)
    }
    const created = await createClaim(payload)
    ok.value = 'Siniestro creado.'
    router.push(`/insurance/claims/${created.id}`)
  }catch(e){
    error.value = String(e?.message || e)
  }finally{
    loading.value = false
  }
}
</script>

<style scoped>
.card{ background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:16px; }
.head{ display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:12px; }
.grid{ display:grid;grid-template-columns: repeat(2, minmax(0,1fr));gap:12px; }
.field{ display:flex;flex-direction:column;gap:6px; }
.full{ grid-column: 1 / -1; }
label{ font-size:12px;color:#6b7280; }
input, select, textarea{
  border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px;outline:none;
}
.actions{ display:flex;justify-content:flex-end; }
.btn{ background:#2563eb;color:#fff;border:none;padding:10px 12px;border-radius:12px;cursor:pointer; }
.btn:disabled{ opacity:.6; cursor:not-allowed; }
.ghost{ text-decoration:none;background:#f3f4f6;border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px;color:#111827; }
.err{ color:#b91c1c; }
.ok{ color:#047857; }
.muted{ color:#6b7280; }
</style>
