<template>
  <div class="loading">Cargando…</div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '../../stores/auth'

const router = useRouter()
const user = computed(() => auth.user() || null)
const role = computed(() => String(user.value?.role || '').toLowerCase())

onMounted(() => {
  // Admin -> summary. Professional -> exports (y opcionalmente "mine")
  if (role.value === 'admin') {
    router.replace('/reports/summary')
  } else {
    router.replace('/reports/exports')
  }
})
</script>

<style scoped>
.loading{ color: var(--muted); font-weight: 900; }
</style>
