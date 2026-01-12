<template>
  <div class="panel">
    <div class="head">
      <h2>Áreas</h2>
      <div class="actions">
        <input v-model.trim="name" class="inp" placeholder="Nombre del área" @keyup.enter="onCreate" />
        <button class="btn" @click="onCreate" :disabled="loading || !name">Agregar</button>
      </div>
    </div>

    <p v-if="error" class="errorBox">{{ error }}</p>

    <div v-if="loading" class="muted">Cargando...</div>

    <div v-else class="table">
      <div class="row headRow">
        <div>Nombre</div>
        <div>Estado</div>
        <div>Acción</div>
      </div>

      <div v-for="a in areas" :key="a.id" class="row">
        <div class="name">
          <span v-if="editId !== a.id">{{ a.name }}</span>

          <input
            v-else
            v-model.trim="editName"
            class="inp"
            style="max-width: 320px"
            @keyup.enter="saveRename(a)"
          />
        </div>

        <div>
          <span class="pill" :class="a.enabled ? 'ok' : 'off'">
            {{ a.enabled ? 'Activa' : 'Inactiva' }}
          </span>
        </div>

        <div class="ops">
          <button class="link" v-if="editId !== a.id" @click="startRename(a)">Renombrar</button>
          <button class="link" v-else @click="saveRename(a)">Guardar</button>
          <button class="link subtle" v-if="editId === a.id" @click="cancelRename">Cancelar</button>

          <button class="link danger" @click="toggle(a)">
            {{ a.enabled ? 'Desactivar' : 'Activar' }}
          </button>
        </div>
      </div>

      <div v-if="areas.length===0" class="empty">
        No hay áreas registradas.
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { listAreas, createArea, patchArea, normalizeApiError } from "../../services/adminApi";

const areas = ref([]);
const name = ref("");
const loading = ref(false);
const error = ref("");

const editId = ref(null);
const editName = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const res = await listAreas();
    areas.value = res.data || [];
  } catch (e) {
    error.value = normalizeApiError(e);
  } finally {
    loading.value = false;
  }
}

async function onCreate() {
  if (!name.value) return;
  error.value = "";
  try {
    await createArea(name.value);
    name.value = "";
    await load();
  } catch (e) {
    // 409 = duplicado -> mensaje simple
    const msg = normalizeApiError(e);
    error.value = msg.includes("409") ? "Ya existe un área con ese nombre." : msg;
    await load();
  }
}

function startRename(a) {
  editId.value = a.id;
  editName.value = a.name;
}

function cancelRename() {
  editId.value = null;
  editName.value = "";
}

async function saveRename(a) {
  if (!editName.value) return;
  error.value = "";
  try {
    await patchArea(a.id, { name: editName.value });
    cancelRename();
    await load();
  } catch (e) {
    error.value = normalizeApiError(e);
  }
}

async function toggle(a) {
  error.value = "";
  try {
    await patchArea(a.id, { enabled: !a.enabled });
    await load();
  } catch (e) {
    error.value = normalizeApiError(e);
  }
}

onMounted(load);
</script>

<style scoped>
.panel{ background:#fff; border:1px solid #e5e7eb; border-radius: 16px; padding: 14px; }
.head{ display:flex; align-items:flex-end; justify-content:space-between; gap: 12px; margin-bottom: 12px; }
.head h2{ margin:0; font-size: 18px; font-weight: 900; color:#111827; }
.actions{ display:flex; gap: 10px; align-items:center; }
.inp{ border:1px solid #e5e7eb; border-radius: 12px; padding: 10px 12px; outline:none; min-width: 240px; }
.inp:focus{ border-color:#93c5fd; box-shadow: 0 0 0 4px rgba(59,130,246,.12); }
.btn{ border:0; padding: 10px 14px; border-radius: 12px; background:#111827; color:#fff; font-weight: 900; cursor:pointer; }
.btn:disabled{ opacity:.5; cursor:not-allowed; }
.muted{ color:#6b7280; font-weight: 800; }

.table{ border:1px solid #f3f4f6; border-radius: 14px; overflow:hidden; }
.row{ display:grid; grid-template-columns: 1fr 130px 260px; gap: 12px; align-items:center; padding: 12px 12px; border-top: 1px solid #f3f4f6; }
.headRow{ background:#f9fafb; border-top:0; font-weight: 900; color:#374151; }
.name{ display:flex; gap: 10px; align-items:center; }
.ops{ display:flex; gap: 10px; align-items:center; justify-content:flex-end; flex-wrap: wrap; }
.link{ border:0; background:transparent; cursor:pointer; font-weight: 900; color:#2563eb; padding: 6px 8px; border-radius: 10px; }
.link:hover{ background:#eff6ff; }
.subtle{ color:#6b7280; }
.danger{ color:#b91c1c; }
.danger:hover{ background:#fff1f2; }

.pill{ display:inline-flex; align-items:center; justify-content:center; padding: 6px 10px; border-radius: 999px; font-weight: 900; font-size: 12px; border:1px solid #e5e7eb; }
.ok{ background:#ecfdf5; color:#065f46; border-color:#a7f3d0; }
.off{ background:#f3f4f6; color:#374151; border-color:#e5e7eb; }

.empty{ padding: 14px; color:#6b7280; font-weight: 800; }
.errorBox{ margin: 0 0 12px; padding: 12px 14px; border-radius: 14px; border:1px solid #fecaca; background:#fff1f2; color:#9f1239; font-weight: 800; }
@media (max-width: 960px){
  .row{ grid-template-columns: 1fr; }
  .ops{ justify-content:flex-start; }
  .actions{ flex-direction: column; align-items: stretch; }
  .inp{ min-width: 0; width: 100%; }
}
</style>
