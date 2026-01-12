<template>
  <div>
    <div class="row">
      <h2 class="h2">Exportaciones</h2>
    </div>

    <div class="form ui-card">
      <div class="f">
        <label>Tipo</label>
        <select v-model="type">
          <option value="cases">Casos</option>
          <option value="appointments">Citas</option>
          <option value="security">Seguridad</option>
          <option value="audit">Auditoría</option>
        </select>
      </div>
      <div class="f">
        <label>Formato</label>
        <select v-model="format">
          <option value="csv">csv</option>
          <option value="xlsx">xlsx</option>
          <option value="pdf">pdf</option>
        </select>
      </div>
      <div class="f">
        <label>Desde</label>
        <input type="date" v-model="from" />
      </div>
      <div class="f">
        <label>Hasta</label>
        <input type="date" v-model="to" />
      </div>

      <div class="actions">
        <button class="btn" @click="create" :disabled="creating">Crear exportación</button>
      </div>
    </div>

    <p v-if="error" class="err">{{ error }}</p>

    <section class="jobs">
      <h3 class="h3">Exportaciones recientes (esta sesión)</h3>
      <div v-if="jobs.length === 0" class="empty">Aún no hay jobs.</div>

      <div v-for="j in jobs" :key="j.job_id" class="job ui-card">
        <div class="jobTop">
          <div>
            <div class="jobId mono">{{ j.job_id }}</div>
            <div class="meta">{{ j.type }} • {{ j.status }}</div>
          </div>
          <div class="jobBtns">
            <button class="ghost" @click="refresh(j.job_id)">Actualizar</button>
            <button class="btn" v-if="j.status === 'ready'" @click="download(j.job_id)">Descargar</button>
          </div>
        </div>
        <p v-if="j.error" class="jobErr">{{ j.error }}</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { createExport, getExportStatus, reportsApi } from '../../services/reportsApi'

function isoDate(d) {
  return d.toISOString().slice(0, 10)
}

const today = new Date()
const weekAgo = new Date(Date.now() - 6 * 24 * 3600 * 1000)

const type = ref('cases')
const format = ref('csv')
const from = ref(isoDate(weekAgo))
const to = ref(isoDate(today))

const creating = ref(false)
const error = ref('')

const jobs = ref([]) // {job_id, status, type, error?}

async function create() {
  error.value = ''
  creating.value = true
  try {
    const payload = {
      type: type.value,
      format: format.value,
      from: from.value,
      to: to.value
    }
    const accepted = await createExport(payload)
    jobs.value.unshift({ job_id: accepted.job_id, status: 'queued', type: payload.type })
    await refresh(accepted.job_id)
  } catch (e) {
    error.value = e?.message || String(e)
  } finally {
    creating.value = false
  }
}

async function refresh(job_id) {
  try {
    const s = await getExportStatus(job_id)
    const idx = jobs.value.findIndex((x) => x.job_id === job_id)
    const row = { job_id, status: s.status, type: s.type, file_path: s.file_path || '', error: s.error || '' }
    if (idx >= 0) jobs.value[idx] = row
    else jobs.value.unshift(row)
  } catch (e) {
    // no rompas UI
    const idx = jobs.value.findIndex((x) => x.job_id === job_id)
    if (idx >= 0) jobs.value[idx].error = e?.message || String(e)
  }
}

async function download(job_id) {
  error.value = ''
  try {
    // intenta obtener extensión desde el status que ya tenemos en memoria
    const current = jobs.value.find((x) => x.job_id === job_id) || {}
    let ext = ''
    if (current.file_path && typeof current.file_path === 'string') {
      const m = current.file_path.match(/\.([a-z0-9]+)$/i)
      if (m) ext = m[1].toLowerCase()
    }

    const resp = await reportsApi.get(`/reports/export/${encodeURIComponent(job_id)}/download`, {
      responseType: 'blob'
    })

    // filename desde header (si viene), sino job_id + extensión
    const cd = resp.headers?.['content-disposition'] || resp.headers?.['Content-Disposition']
    let filename = ''
    if (cd && typeof cd === 'string') {
      const m2 = cd.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i)
      filename = decodeURIComponent((m2?.[1] || m2?.[2] || '').trim())
    }
    if (!filename) filename = ext ? `${job_id}.${ext}` : `${job_id}`

    const blob = new Blob([resp.data], { type: resp.data?.type || 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e?.message || String(e)
  }
}


let timer = null
onMounted(() => {
  // polling ligero mientras haya jobs en progreso
  timer = window.setInterval(() => {
    const pending = jobs.value.filter((j) => ['queued', 'running'].includes(j.status))
    pending.slice(0, 5).forEach((j) => refresh(j.job_id))
  }, 5000)
})

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.row{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom: 6px; }
.h2{ margin:0; font-size: 18px; font-weight: 900; }
.tip{ margin: 8px 0 12px; color: var(--muted); }
.form{ padding: 12px; border-radius: 14px; display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.f{ display:flex; flex-direction:column; gap:6px; }
.f label{ color: var(--muted); font-weight: 800; font-size: 0.85rem; }
.f input,.f select{ padding: 9px 10px; border-radius: 12px; border: 1px solid var(--border); background:#fff; font-weight: 700; }
.actions{ grid-column: 1 / -1; display:flex; justify-content:flex-end; }
.btn{ padding:8px 12px; border-radius: 12px; border: 1px solid #111827; background:#111827; color:#fff; font-weight: 900; cursor:pointer; }
.ghost{ padding:8px 12px; border-radius: 12px; border: 1px solid var(--border); background:#fff; font-weight: 900; cursor:pointer; }
.err{ margin: 10px 0; color:#b91c1c; font-weight: 800; }
.jobs{ margin-top: 14px; }
.h3{ margin: 0 0 10px; font-size: 14px; font-weight: 900; }
.job{ padding: 12px; border-radius: 14px; margin-bottom: 10px; }
.jobTop{ display:flex; align-items:flex-start; justify-content:space-between; gap: 12px; }
.jobId{ font-weight: 900; }
.meta{ color: var(--muted); font-weight: 800; margin-top: 4px; }
.jobBtns{ display:flex; gap: 8px; }
.jobErr{ margin: 10px 0 0; color:#b91c1c; font-weight: 800; }
.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 0.9rem; }
.empty{ color: var(--muted); }
@media (max-width: 980px){
  .form{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
