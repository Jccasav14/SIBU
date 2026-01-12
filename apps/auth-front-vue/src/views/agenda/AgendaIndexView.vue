<template>
  <div class="loadingCard">
    <div class="spinner"></div>
    <div>
      <div class="t">Cargando agenda…</div>
      <div class="s">Preparando tu vista según el rol.</div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '../../stores/auth'

const router = useRouter()

onMounted(() => {
  const user = auth.user()
  const role = String(user?.role || '').toLowerCase()
  if (role === 'admin') router.replace('/agenda/admin')
  else router.replace('/agenda/me')
})
</script>

<style scoped>
.loadingCard{
  background:#fff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 16px;
  display:flex;
  align-items:center;
  gap: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,.06);
}
.t{ font-weight: 900; color:#111827; }
.s{ color:#6b7280; font-size: 13px; margin-top: 2px; }
.spinner{
  width: 18px; height: 18px;
  border-radius: 50%;
  border: 3px solid #e5e7eb;
  border-top-color: #2563eb;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
