<template>
  <div class="panel">
    <div class="head">
      <h2>Controles</h2>
      <p class="muted">Activa o desactiva opciones del sistema.</p>
    </div>

    <p v-if="error" class="errorBox">{{ error }}</p>

    <div v-if="loading" class="muted">Cargando...</div>

    <div v-else class="list">
      <div class="item" v-for="f in flags" :key="f.key">
        <div class="info">
          <div class="title">{{ prettyFlag(f.key) }}</div>
          <div class="sub">{{ f.key.replaceAll('_',' ') }}</div>
        </div>

        <label class="switch">
          <input type="checkbox" :checked="!!f.enabled" @change="toggle(f)" />
          <span class="slider" />
        </label>
      </div>

      <div v-if="flags.length===0" class="empty">No hay controles configurados.</div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { listFlags, setFlag, normalizeApiError } from "../../services/adminApi";

const flags = ref([]);
const loading = ref(false);
const error = ref("");

function prettyFlag(key) {
  const map = {
    maintenance_mode: "Modo mantenimiento",
    reports_professional_can_view_mine: "Reportes: ver propios"
  };
  return map[key] || key.replaceAll("_", " ");
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const res = await listFlags();
    flags.value = res.data || [];
  } catch (e) {
    error.value = normalizeApiError(e);
  } finally {
    loading.value = false;
  }
}

async function toggle(f) {
  error.value = "";
  try {
    await setFlag(f.key, !f.enabled);
    await load();
  } catch (e) {
    error.value = normalizeApiError(e);
  }
}

onMounted(load);
</script>

<style scoped>
.panel{ background:#fff; border:1px solid #e5e7eb; border-radius: 16px; padding: 14px; }
.head{ margin-bottom: 12px; }
.head h2{ margin:0; font-size: 18px; font-weight: 900; color:#111827; }
.muted{ margin:6px 0 0; color:#6b7280; font-weight: 800; }
.list{ display:flex; flex-direction: column; gap: 10px; }
.item{ display:flex; align-items:center; justify-content:space-between; gap: 12px; padding: 12px; border:1px solid #f3f4f6; border-radius: 14px; background:#fbfdff; }
.info{ display:flex; flex-direction:column; gap: 2px; }
.title{ font-weight: 900; color:#111827; }
.sub{ color:#6b7280; font-weight: 800; font-size: 12px; }
.empty{ color:#6b7280; font-weight: 800; padding: 12px; }

.switch{ position: relative; display: inline-block; width: 44px; height: 26px; }
.switch input{ opacity: 0; width: 0; height: 0; }
.slider{ position:absolute; cursor:pointer; inset:0; background:#e5e7eb; border-radius: 999px; transition: .2s; border:1px solid #d1d5db; }
.slider:before{ position:absolute; content:""; height: 20px; width: 20px; left: 3px; top: 2px; background:white; border-radius: 999px; transition: .2s; box-shadow: 0 1px 2px rgba(0,0,0,.15); }
.switch input:checked + .slider{ background:#2563eb; border-color:#1d4ed8; }
.switch input:checked + .slider:before{ transform: translateX(18px); }

.errorBox{ margin: 0 0 12px; padding: 12px 14px; border-radius: 14px; border:1px solid #fecaca; background:#fff1f2; color:#9f1239; font-weight: 800; }
</style>
