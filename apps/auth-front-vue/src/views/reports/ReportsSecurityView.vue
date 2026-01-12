<template>
  <div>
    <div class="row">
      <h2 class="h2">Seguridad</h2>
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
    </div>

    <p v-if="error" class="err">{{ error }}</p>

    <table class="table" v-if="rows.length">
      <thead>
        <tr>
          <th>Día</th>
          <th class="num">Login failed</th>
          <th class="num">Access denied</th>
          <th class="num">Suspicious</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.day">
          <td>{{ r.day }}</td>
          <td class="num">{{ r.login_failed }}</td>
          <td class="num">{{ r.access_denied }}</td>
          <td class="num">{{ r.suspicious_activity }}</td>
        </tr>
      </tbody>
    </table>

    <p v-else class="empty">Sin datos</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getSecurity } from '../../services/reportsApi'

function isoDate(d) {
  return d.toISOString().slice(0, 10)
}

const today = new Date()
const weekAgo = new Date(Date.now() - 6 * 24 * 3600 * 1000)
const from = ref(isoDate(weekAgo))
const to = ref(isoDate(today))

const rows = ref([])
const loading = ref(false)
const error = ref('')

async function load() {
  error.value = ''
  loading.value = true
  try {
    rows.value = await getSecurity({ from: from.value, to: to.value })
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
.filters{ margin: 10px 0 12px; padding: 12px; border-radius: 14px; display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.f{ display:flex; flex-direction:column; gap: 6px; }
.f label{ color: var(--muted); font-weight: 800; font-size: 0.85rem; }
.f input{ padding: 9px 10px; border-radius: 12px; border: 1px solid var(--border); background:#fff; font-weight: 700; }
.err{ margin: 10px 0; color:#b91c1c; font-weight: 800; }
.table{ width:100%; border-collapse: collapse; }
.table th,.table td{ border-bottom: 1px solid var(--border); padding: 10px 8px; text-align:left; }
.table th{ color: var(--muted); font-size: 0.85rem; }
.num{ text-align:right; font-weight: 900; }
.empty{ color: var(--muted); margin: 8px 0; }
</style>
