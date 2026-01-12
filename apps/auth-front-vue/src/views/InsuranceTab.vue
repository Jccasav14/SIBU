<template>
  <div class="wrap">
    <section class="card">
      <header class="head">
        <h2>Perfil Seguros</h2>
        <button class="btn" @click="load" :disabled="loading">Actualizar</button>
      </header>

      <p v-if="loading"><small class="muted">Cargando...</small></p>
      <p v-if="error" class="err">{{ error }}</p>
      <p v-if="ok" class="ok">{{ ok }}</p>
      <p v-if="err" class="err">{{ err }}</p>

      <div v-if="me" class="grid">
        <div class="field">
          <label>Email</label>
          <input :value="me.email" disabled />
        </div>

        <div class="field">
          <label>Rol</label>
          <input :value="me.role" disabled />
        </div>

        <div class="field full">
          <label>Nombre completo</label>
          <input v-model="form.full_name" placeholder="Nombre" />
        </div>

        <div class="field">
          <label>Teléfono</label>
          <input v-model="form.phone" placeholder="Teléfono" />
        </div>

        <div class="field full">
          <label>Bio</label>
          <textarea v-model="form.bio" rows="4" placeholder="Información del agente de seguros..."></textarea>
        </div>

        <div class="actions full">
          <button class="btn" @click="save" :disabled="saving">
            {{ saving ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </div>
      </div>
    </section>

    <section class="card note">
      <h3>Módulo Seguros</h3>
      <p class="muted">
        Aquí solo ingresan roles <b>insurance</b> y <b>admin</b>.
        Desde el menú “Seguros / Siniestros” puedes crear, revisar, aprobar/rechazar y registrar pagos.
      </p>
      <RouterLink class="ghost" to="/insurance/overview">Ir al panel de seguros</RouterLink>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getMe, updateMe } from '../services/usersApi'

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const ok = ref('')
const err = ref('')
const me = ref(null)

const form = reactive({ full_name:'', phone:'', bio:'' })

function sync(){
  form.full_name = me.value?.full_name || ''
  form.phone = me.value?.phone || ''
  form.bio = me.value?.bio || ''
}

async function load(){
  loading.value = true
  error.value = ''
  try{
    me.value = await getMe()
    sync()
  }catch(e){
    error.value = String(e?.message || e)
  }finally{
    loading.value = false
  }
}

async function save(){
  saving.value = true
  ok.value = ''
  err.value = ''
  try{
    const updated = await updateMe({ ...form })
    me.value = updated
    ok.value = 'Perfil actualizado.'
  }catch(e){
    err.value = String(e?.message || e)
  }finally{
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.wrap{
  max-width: 900px;
  margin: 0 auto;
  padding: 18px;
  display:flex;
  flex-direction:column;
  gap: 14px;
}
.card{
  background:#fff;
  border:1px solid #e5e7eb;
  border-radius:14px;
  padding:16px;
}
.head{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom: 12px;
}
.grid{
  display:grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap:12px;
}
.field{ display:flex; flex-direction:column; gap:6px; }
.full{ grid-column: 1 / -1; }
label{ font-size:12px;color:#6b7280; }
input, textarea{
  border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px;outline:none;
}
.actions{ display:flex; justify-content:flex-end; }
.btn{ background:#2563eb;color:#fff;border:none;padding:10px 12px;border-radius:12px;cursor:pointer; }
.btn:disabled{ opacity:.6; cursor:not-allowed; }
.ghost{ text-decoration:none;background:#f3f4f6;border:1px solid #e5e7eb;border-radius:12px;padding:10px 12px;color:#111827; }
.ok{ color:#047857; }
.err{ color:#b91c1c; }
.muted{ color:#6b7280; }
.note h3{ margin-top:0; }
</style>
