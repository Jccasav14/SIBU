<template>
  <div>
    <div class="row">
      <h2 class="h2">Mine</h2>
      <button class="btn" @click="load" :disabled="loading">Actualizar</button>
    </div>

    <p class="tip">
      Esta vista usa <code>/reports/mine</code> y solo funciona si el backend habilita <code>REPORTS_PROFESSIONAL_CAN_VIEW_MINE=true</code>.
    </p>

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

    <div v-if="data" class="card ui-card">
      <div class="k">Actor</div>
      <div class="v mono">{{ data.actor }}</div>

      <div class="grid">
        <div>
          <div class="k">Rol</div>
          <div class="v">{{ data.role }}</div>
        </div>
        <div>
          <div class="k">Eventos</div>
          <div class="v">{{ data.count }}</div>
        </div>
        <div>
          <div class="k">Desde</div>
          <div class="v">{{ data.from }}</div>
        </div>
        <div>
          <div class="k">Hasta</div>
          <div class="v">{{ data.to }}</div>
        </div>
      </div>
    </div>

    <p v-else class="empty">Sin datos</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getMine } from '../../services/reportsApi'

function isoDate(d) {
  return d.toISOString().slice(0, 10)
}

const today = new Date()
const weekAgo = new Date(Date.now() - 6 * 24 * 3600 * 1000)
const from = ref(isoDate(weekAgo))
const to = ref(isoDate(today))

const data = ref(null)
const loading = ref(false)
const error = ref('')

async function load() {
  error.value = ''
  loading.value = true
  try {
    data.value = await getMine({ from: from.value, to: to.value })
  } catch (e) {
    error.value = e?.message || String(e)
    data.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.row{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom: 6px; }
.h2{ margin:0; font-size: 18px; font-weight: 900; }
.btn{ padding:8px 12px; border-radius: 12px; border: 1px solid #111827; background:#111827; color:#fff; font-weight: 900; cursor:pointer; }
.btn:disabled{ opacity: .6; cursor: not-allowed; }
.tip{ margin: 10px 0 12px; color: var(--muted); }
.filters{ margin: 10px 0 12px; padding: 12px; border-radius: 14px; display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.f{ display:flex; flex-direction:column; gap: 6px; }
.f label{ color: var(--muted); font-weight: 800; font-size: 0.85rem; }
.f input{ padding: 9px 10px; border-radius: 12px; border: 1px solid var(--border); background:#fff; font-weight: 700; }
.err{ margin: 10px 0; color:#b91c1c; font-weight: 800; }
.card{ padding: 12px; border-radius: 14px; }
.k{ color: var(--muted); font-weight: 800; font-size: 0.85rem; }
.v{ margin-top: 4px; font-weight: 900; }
.grid{ margin-top: 12px; display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 0.9rem; }
.empty{ color: var(--muted); }
@media (max-width: 980px){
  .grid{ grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
