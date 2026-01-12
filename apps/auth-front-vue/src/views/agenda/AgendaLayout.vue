<template>
  <div class="page">
    <header class="pageHead">
      <h1>Agenda</h1>
      <p class="muted">Citas y disponibilidad (vista semanal)</p>
    </header>

    <RouterView />
  </div>
</template>

<script setup>
// This is a layout wrapper for /agenda routes
</script>

<style scoped>
.page{ padding: 18px; max-width: 1280px; margin: 0 auto; }
.pageHead{ display:flex; align-items:flex-end; justify-content:space-between; gap: 12px; margin-bottom: 14px; }
.pageHead h1{ margin:0; font-size: 24px; font-weight: 900; color:#111827; }
.muted{ margin:0; color:#6b7280; }
@media (max-width: 720px){
  .pageHead{ flex-direction:column; align-items:flex-start; }
}
</style>
