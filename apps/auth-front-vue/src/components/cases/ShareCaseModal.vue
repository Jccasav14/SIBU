<template>
  <div class="backdrop" @mousedown.self="$emit('close')">
    <div class="modal">
      <div class="head">
        <h3>Compartir caso</h3>
        <button class="x" @click="$emit('close')">✕</button>
      </div>

      <div class="tabs">
        <button class="tab" :class="{on: mode==='user'}" @click="mode='user'">Con usuario</button>
        <button class="tab" :class="{on: mode==='area'}" @click="mode='area'">Con área</button>
      </div>

      <!-- Con usuario -->
      <div v-if="mode==='user'" class="box">
        <p class="muted">
          Comparte con un profesional específico.
          <span v-if="isAdmin">Puedes buscar por correo o pegar el ID de usuario.</span>
          <span v-else>Ingresa el <b>ID de usuario</b> del profesional.</span>
        </p>

        <div class="grid">
          <template v-if="isAdmin">
            <div class="field">
              <label>Correo (solo admin)</label>
              <input v-model.trim="email" placeholder="pro@uce.edu.ec" />
              <small class="hint">Si llenas el correo, resolvemos el ID de usuario automáticamente.</small>
            </div>
          </template>

          <div class="field">
            <label>ID de usuario</label>
            <input v-model.trim="userId" placeholder="UUID / ID" />
          </div>

          <div class="field">
            <label>Permiso</label>
            <select v-model="permission">
              <option value="READ">Solo lectura</option>
              <option value="WRITE">Edición permitida</option>
            </select>
          </div>

          <div class="actions">
            <button class="btn" @click="$emit('close')">Cancelar</button>
            <button class="btn primary" :disabled="loading || (!userId && !(isAdmin && email))" @click="submitUser">
              {{ loading ? 'Compartiendo...' : 'Compartir' }}
            </button>
          </div>
        </div>

        <p v-if="err" class="err">{{ err }}</p>
        <p v-if="ok" class="ok">{{ ok }}</p>
      </div>

      <!-- Con área -->
      <div v-else class="box">
        <p class="muted">Comparte con un área completa.</p>

        <div class="grid">
          <div class="field">
            <label>Área</label>
            <select v-model="area">
              <option value="GENERAL">General</option>
              <option value="PSY">Psicología</option>
              <option value="SOCIAL">Trabajo Social</option>
              <option value="MEDICAL">Médica</option>
              <option value="LEGAL">Legal</option>
            </select>
          </div>

          <div class="field">
            <label>Permiso</label>
            <select v-model="permission">
              <option value="READ">Solo lectura</option>
              <option value="WRITE">Edición permitida</option>
            </select>
          </div>

          <div class="actions">
            <button class="btn" @click="$emit('close')">Cancelar</button>
            <button class="btn primary" :disabled="loading || !area" @click="submitArea">
              {{ loading ? 'Compartiendo...' : 'Compartir' }}
            </button>
          </div>
        </div>

        <p v-if="err" class="err">{{ err }}</p>
        <p v-if="ok" class="ok">{{ ok }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { auth } from '../../stores/auth'
import { adminGetUserByEmail } from '../../services/usersApi'

defineProps({
  caseId: { type: String, required: true }
})

const emit = defineEmits(['close', 'submit', 'shared'])

const role = computed(() => String(auth.user()?.role || '').toLowerCase())
const isAdmin = computed(() => role.value === 'admin')

const mode = ref('user')
const email = ref('')
const userId = ref('')
const area = ref('GENERAL')
const permission = ref('READ')

const loading = ref(false)
const err = ref('')
const ok = ref('')

async function submitUser() {
  err.value = ''
  ok.value = ''
  loading.value = true
  try {
    let uid = userId.value

    if (!uid && isAdmin.value && email.value) {
      const u = await adminGetUserByEmail(email.value)
      uid = u?.id || u?.user_id || u?.sub || ''
      if (!uid) throw new Error('No se pudo resolver user_id desde el email.')
      userId.value = uid
    }

    emit('submit', { user_id: uid, permission: permission.value })
    ok.value = 'Compartido ✅'
    emit('shared')
  } catch (e) {
    err.value = e?.message || 'Error compartiendo'
  } finally {
    loading.value = false
  }
}

async function submitArea() {
  err.value = ''
  ok.value = ''
  loading.value = true
  try {
    emit('submit', { area: area.value, permission: permission.value })
    ok.value = 'Compartido ✅'
    emit('shared')
  } catch (e) {
    err.value = e?.message || 'Error compartiendo'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.backdrop { position: fixed; inset: 0; background: rgba(15,23,42,0.35); display: flex; align-items: center; justify-content: center; padding: 18px; z-index: 100; }
.modal { width: min(720px, 100%); background: #fff; border-radius: 16px; border: 1px solid #e5e7eb; box-shadow: 0 18px 50px rgba(0,0,0,0.18); padding: 14px; }
.head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 6px 6px 10px; }
.head h3 { margin: 0; font-size: 1.1rem; }
.x { border: none; background: transparent; cursor: pointer; font-size: 1.1rem; color: #6b7280; }
.tabs { display: flex; gap: 8px; padding: 0 6px 10px; }
.tab { border: 1px solid #e5e7eb; background: #fff; border-radius: 999px; padding: 8px 12px; cursor: pointer; font-weight: 700; color: #111827; }
.tab.on { background: #2563eb; border-color: #2563eb; color: #fff; }
.box { padding: 6px; }
.muted { color: #6b7280; margin: 0 0 10px; }
.hint { color: #6b7280; font-size: 0.8rem; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 12px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 0.85rem; font-weight: 600; color: #374151; }
.field input, .field select { padding: 10px 12px; border-radius: 10px; border: 1px solid #d1d5db; }
.field input:focus, .field select:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15); }
.actions { grid-column: 1 / -1; display: flex; justify-content: flex-end; gap: 10px; margin-top: 4px; }
.btn { padding: 8px 14px; border-radius: 10px; border: 1px solid #d1d5db; background: #f9fafb; cursor: pointer; font-weight: 700; }
.btn.primary { background: #2563eb; border-color: #2563eb; color: #fff; }
.btn.primary:hover { background: #1e40af; }
.err { margin-top: 10px; color: #b91c1c; background: #fef2f2; padding: 10px 12px; border-radius: 10px; border: 1px solid #fecaca; }
.ok { margin-top: 10px; color: #065f46; background: #ecfdf5; padding: 10px 12px; border-radius: 10px; border: 1px solid #a7f3d0; }
@media (max-width: 700px) { .grid { grid-template-columns: 1fr; } }
</style>
