<template>
  <div class="ui">
    <header class="pageHead">
      <div>
        <h1>Administración</h1>
        <p class="muted">Panel de control</p>
      </div>

      <div class="badge" v-if="roleLabel">
        <span class="dot" aria-hidden="true" />
        <span>{{ roleLabel }}</span>
      </div>
    </header>

    <nav class="tabs" aria-label="Secciones de administración">
      <button class="tab" :class="{ active: tab==='overview' }" @click="tab='overview'">Resumen</button>
      <button class="tab" :class="{ active: tab==='areas' }" @click="tab='areas'">Áreas</button>
      <button class="tab" :class="{ active: tab==='flags' }" @click="tab='flags'">Controles</button>
    </nav>

    <section v-if="tab==='overview'" class="grid">
      <div class="card">
        <h3>Estado</h3>
        <div class="kv">
          <div class="k">Servicio</div><div class="v">Admin</div>
          <div class="k">Cache</div><div class="v">{{ overview?.cache?.status || 'OK' }}</div>
        </div>
      </div>

      <div class="card">
        <h3>Indicadores</h3>
        <div class="kv">
          <div class="k">Áreas</div><div class="v">{{ overview?.counts?.areas ?? '—' }}</div>
          <div class="k">Servicios</div><div class="v">{{ overview?.counts?.services ?? '—' }}</div>
          <div class="k">Acciones</div><div class="v">{{ overview?.counts?.actions ?? '—' }}</div>
        </div>
      </div>

      <div class="card">
        <h3>Controles principales</h3>
        <div class="flagRow" v-for="f in (overview?.flags || [])" :key="f.key">
          <span class="flagKey">{{ prettyFlag(f.key) }}</span>
          <label class="switch">
            <input type="checkbox" :checked="!!f.enabled" @change="toggleFlag(f)" />
            <span class="slider" />
          </label>
        </div>
        <p v-if="(overview?.flags || []).length===0" class="muted">Sin controles configurados.</p>
      </div>
    </section>

    <section v-else-if="tab==='areas'">
      <CatalogAreas />
    </section>

    <section v-else>
      <FlagsPanel />
    </section>

    <p v-if="error" class="errorBox">{{ error }}</p>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { auth } from "../../stores/auth";
import { getOverview, setFlag, normalizeApiError } from "../../services/adminApi";
import CatalogAreas from "./CatalogAreas.vue";
import FlagsPanel from "./FlagsPanel.vue";

const tab = ref("overview");
const overview = ref(null);
const error = ref("");

const roleLabel = computed(() => {
  const u = auth.user();
  const role = String(u?.role || "").toLowerCase();
  if (!role) return "";
  if (role === "admin") return "Admin";
  if (role === "professional") return "Profesional";
  return role;
});

function prettyFlag(key) {
  const map = {
    maintenance_mode: "Modo mantenimiento",
    reports_professional_can_view_mine: "Reportes: ver propios"
  };
  return map[key] || key.replaceAll("_", " ");
}

async function load() {
  error.value = "";
  try {
    const res = await getOverview();
    overview.value = res.data;
  } catch (e) {
    error.value = normalizeApiError(e);
  }
}

async function toggleFlag(f) {
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
.ui{ padding: 18px; max-width: 1280px; margin: 0 auto; }
.pageHead{ display:flex; align-items:flex-end; justify-content:space-between; gap: 12px; margin-bottom: 12px; }
.pageHead h1{ margin:0; font-size: 24px; font-weight: 900; color:#111827; }
.muted{ margin:6px 0 0; color:#6b7280; }

.badge{ display:flex; align-items:center; gap:10px; padding: 8px 12px; border-radius: 999px;
  background: #f3f4f6; border: 1px solid #e5e7eb; color:#111827; font-weight: 800; }
.dot{ width:10px; height:10px; border-radius: 50%; background:#2563eb; display:inline-block; }

.tabs{ display:flex; gap: 10px; align-items:center; margin: 12px 0 16px; padding: 6px; background:#f3f4f6; border:1px solid #e5e7eb; border-radius: 14px; width: fit-content;}
.tab{ border:0; background:transparent; padding: 10px 12px; border-radius: 10px; font-weight: 900; color:#374151; cursor:pointer; }
.tab.active{ background:#ffffff; border:1px solid #e5e7eb; color:#111827; box-shadow: 0 1px 0 rgba(0,0,0,.03); }

.grid{ display:grid; grid-template-columns: repeat(12, 1fr); gap: 12px; }
.card{ grid-column: span 4; background:#fff; border:1px solid #e5e7eb; border-radius: 16px; padding: 14px; }
.card h3{ margin:0 0 10px; font-size: 14px; letter-spacing: .2px; color:#111827; }

.kv{ display:grid; grid-template-columns: 1fr auto; gap: 8px 10px; }
.k{ color:#6b7280; font-weight: 800; font-size: 12px; }
.v{ color:#111827; font-weight: 900; font-size: 13px; }

.flagRow{ display:flex; align-items:center; justify-content:space-between; gap: 10px; padding: 8px 0; border-top: 1px solid #f3f4f6; }
.flagRow:first-of-type{ border-top: 0; padding-top: 0; }
.flagKey{ font-weight: 900; color:#111827; font-size: 13px; }

/* Switch */
.switch{ position: relative; display: inline-block; width: 44px; height: 26px; }
.switch input{ opacity: 0; width: 0; height: 0; }
.slider{ position:absolute; cursor:pointer; inset:0; background:#e5e7eb; border-radius: 999px; transition: .2s; border:1px solid #d1d5db; }
.slider:before{ position:absolute; content:""; height: 20px; width: 20px; left: 3px; top: 2px; background:white; border-radius: 999px; transition: .2s; box-shadow: 0 1px 2px rgba(0,0,0,.15); }
.switch input:checked + .slider{ background:#2563eb; border-color:#1d4ed8; }
.switch input:checked + .slider:before{ transform: translateX(18px); }

.errorBox{ margin-top: 14px; padding: 12px 14px; border-radius: 14px; border:1px solid #fecaca; background:#fff1f2; color:#9f1239; font-weight: 800; }
@media (max-width: 960px){
  .card{ grid-column: span 12; }
}
</style>
