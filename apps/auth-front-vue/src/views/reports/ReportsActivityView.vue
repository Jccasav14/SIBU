<template>
  <div>
    <div class="row">
      <h2 class="h2">Actividad</h2>
      <button class="btn" @click="load" :disabled="loading">Actualizar</button>
    </div>

    <div class="filters ui-card">
      <div class="f">
        <label>Desde</label>
        <input type="date" v-model="from" />
      </div>
      <div class="f">
        <label>Hasta</label>
        <input type="date" v-model="to" />
      </div>
      <div class="f">
        <label>Servicio</label>
        <input v-model.trim="service" placeholder="reports/audit/cases..." />
      </div>
      <div class="f">
        <label>event_type</label>
        <input v-model.trim="event_type" placeholder="CASE_CREATED..." />
      </div>
      <div class="f">
        <label>severity</label>
        <input v-model.trim="severity" placeholder="info|warn|error" />
      </div>
      <div class="f">
        <label>role</label>
        <input v-model.trim="role" placeholder="admin|professional" />
      </div>
    </div>

    <p v-if="error" class="err">{{ error }}</p>

    <table class="table" v-if="rows.length">
      <thead>
        <tr>
          <th>Día</th>
          <th>Servicio</th>
          <th>Tipo</th>
          <th>Severidad</th>
          <th>Rol</th>
          <th class="num">Count</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.day + r.service + r.event_type + r.severity + r.role">
          <td>{{ r.day }}</td>
          <td>{{ r.service }}</td>
          <td class="mono">{{ r.event_type }}</td>
          <td>{{ r.severity }}</td>
          <td>{{ r.role }}</td>
          <td class="num">{{ r.count }}</td>
        </tr>
      </tbody>
    </table>

    <p v-else class="empty">Sin datos</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getActivity } from '../../services/reportsApi'

function isoDate(d) {
  return d.toISOString().slice(0, 10)
}

const today = new Date()
const weekAgo = new Date(Date.now() - 6 * 24 * 3600 * 1000)

const from = ref(isoDate(weekAgo))
const to = ref(isoDate(today))

const service = ref('')
const event_type = ref('')
const severity = ref('')
const role = ref('')

const rows = ref([])
const loading = ref(false)
const error = ref('')

async function load() {
  error.value = ''
  loading.value = true
  try {
    const params = {
      from: from.value,
      to: to.value,
      ...(service.value ? { service: service.value } : {}),
      ...(event_type.value ? { event_type: event_type.value } : {}),
      ...(severity.value ? { severity: severity.value } : {}),
      ...(role.value ? { role: role.value } : {})
    }
    rows.value = await getActivity(params)
  } catch (e) {
    error.value = e?.message || String(e)
    rows.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.row{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom: 10px; }
.h2{ margin:0; font-size: 18px; font-weight: 900; }
.btn{ padding:8px 12px; border-radius: 12px; border: 1px solid #111827; background:#111827; color:#fff; font-weight: 900; cursor:pointer; }
.btn:disabled{ opacity: .6; cursor: not-allowed; }
.filters{ margin: 10px 0 12px; padding: 12px; border-radius: 14px; display:grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; }
.f{ display:flex; flex-direction:column; gap: 6px; }
.f label{ color: var(--muted); font-weight: 800; font-size: 0.85rem; }
.f input{ padding: 9px 10px; border-radius: 12px; border: 1px solid var(--border); background:#fff; font-weight: 700; }
.err{ margin: 10px 0; color:#b91c1c; font-weight: 800; }
.table{ width:100%; border-collapse: collapse; }
.table th,.table td{ border-bottom: 1px solid var(--border); padding: 10px 8px; text-align:left; }
.table th{ color: var(--muted); font-size: 0.85rem; }
.num{ text-align:right; font-weight: 900; }
.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 0.9rem; }
.empty{ color: var(--muted); margin: 8px 0; }
@media (max-width: 980px){
  .filters{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
