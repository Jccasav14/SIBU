<template>
  <div class="page">
    <header class="pageHead">
      <div>
        <h1>Reportes</h1>
      </div>

      <div class="rolePill" :class="role">
        <span class="dot" aria-hidden="true" />
        <span>{{ roleLabel }}</span>
      </div>
    </header>

    <nav class="tabs" aria-label="Reports sections">
      <RouterLink class="tab" to="/reports/summary" v-if="isAdmin">Resumen</RouterLink>
      <RouterLink class="tab" to="/reports/activity" v-if="isAdmin">Actividad</RouterLink>
      <RouterLink class="tab" to="/reports/cases" v-if="isAdmin">Casos</RouterLink>
      <RouterLink class="tab" to="/reports/appointments" v-if="isAdmin">Citas</RouterLink>
      <RouterLink class="tab" to="/reports/security" v-if="isAdmin">Seguridad</RouterLink>

      <RouterLink class="tab" to="/reports/exports">Exportaciones</RouterLink>
      <RouterLink class="tab" to="/reports/mine" v-if="isPro">Mine</RouterLink>
    </nav>

    <section class="content ui-card">
      <RouterView />
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { auth } from '../../stores/auth'

const user = computed(() => auth.user() || null)
const role = computed(() => String(user.value?.role || '').toLowerCase())
const isAdmin = computed(() => role.value === 'admin')
const isPro = computed(() => role.value === 'professional')
const roleLabel = computed(() => (isAdmin.value ? 'Admin' : isPro.value ? 'Professional' : 'User'))
</script>

<style scoped>
.page{ padding: 18px; max-width: 1280px; margin: 0 auto; }
.pageHead{ display:flex; align-items:flex-end; justify-content:space-between; gap: 12px; margin-bottom: 12px; }
.pageHead h1{ margin:0; font-size: 24px; font-weight: 900; color:#111827; }
.muted{ margin:6px 0 0; color:#6b7280; }

.rolePill{ display:flex; align-items:center; gap:10px; padding: 8px 12px; border-radius: 999px; border: 1px solid var(--border); background: #fff; font-weight: 800; }
.rolePill .dot{ width: 10px; height: 10px; border-radius: 999px; background: #94a3b8; }
.rolePill.admin{ border-color:#bfdbfe; background:#eff6ff; }
.rolePill.admin .dot{ background:#2563eb; }
.rolePill.professional{ border-color:#bbf7d0; background:#f0fdf4; }
.rolePill.professional .dot{ background:#16a34a; }

.tabs{ display:flex; flex-wrap:wrap; gap: 8px; margin: 8px 0 14px; }
.tab{ text-decoration:none; padding: 8px 12px; border-radius: 12px; border:1px solid transparent; background: rgba(255,255,255,0.8); font-weight: 800; color:#0f172a; }
.tab:hover{ background:#fff; border-color: var(--border); }
.tab.router-link-active{ background:#111827; color:#fff; }

.content{ padding: 14px; }
@media (max-width: 720px){
  .pageHead{ flex-direction:column; align-items:flex-start; }
}
</style>
