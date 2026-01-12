<template>
  <div class="backdrop" @mousedown.self="$emit('close')">
    <div class="modal">
      <div class="head">
        <h3>Asignar caso</h3>
        <button class="x" @click="$emit('close')">✕</button>
      </div>

      <p class="muted">Ingresa el <b>professional_id</b> (o pega el id del usuario profesional).</p>

      <div class="field">
        <label>Professional ID</label>
        <input v-model.trim="professionalId" placeholder="uuid / id" />
      </div>

      <div class="actions">
        <button class="btn" @click="$emit('close')">Cancelar</button>
        <button class="btn primary" :disabled="loading || !professionalId" @click="submit">
          {{ loading ? 'Asignando...' : 'Asignar' }}
        </button>
      </div>

      <p v-if="err" class="err">{{ err }}</p>
      <p v-if="ok" class="ok">{{ ok }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  caseId: { type: String, required: true }
})
const emit = defineEmits(['close','submit','assigned'])

const professionalId = ref('')
const loading = ref(false)
const err = ref('')
const ok = ref('')

async function submit() {
  err.value = ''
  ok.value = ''
  loading.value = true
  try {
    emit('submit', professionalId.value)
    ok.value = 'Asignado ✅'
    emit('assigned')
  } catch (e) {
    err.value = e?.message || 'Error asignando'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.backdrop { position: fixed; inset: 0; background: rgba(15,23,42,0.35); display: flex; align-items: center; justify-content: center; padding: 18px; z-index: 100; }
.modal { width: min(540px, 100%); background: #fff; border-radius: 16px; border: 1px solid #e5e7eb; box-shadow: 0 18px 50px rgba(0,0,0,0.18); padding: 14px; }
.head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 6px 6px 10px; }
.head h3 { margin: 0; font-size: 1.1rem; }
.x { border: none; background: transparent; cursor: pointer; font-size: 1.1rem; color: #6b7280; }
.muted { color: #6b7280; margin: 0 6px 10px; }
.field { display: flex; flex-direction: column; gap: 6px; padding: 0 6px; }
.field label { font-size: 0.85rem; font-weight: 600; color: #374151; }
.field input { padding: 10px 12px; border-radius: 10px; border: 1px solid #d1d5db; }
.field input:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15); }
.actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 12px; padding: 0 6px; }
.btn { padding: 8px 14px; border-radius: 10px; border: 1px solid #d1d5db; background: #f9fafb; cursor: pointer; font-weight: 700; }
.btn.primary { background: #2563eb; border-color: #2563eb; color: #fff; }
.btn.primary:hover { background: #1e40af; }
.err { margin: 10px 6px 0; color: #b91c1c; background: #fef2f2; padding: 10px 12px; border-radius: 10px; border: 1px solid #fecaca; }
.ok { margin: 10px 6px 0; color: #065f46; background: #ecfdf5; padding: 10px 12px; border-radius: 10px; border: 1px solid #a7f3d0; }
</style>
