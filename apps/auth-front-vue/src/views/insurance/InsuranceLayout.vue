<template>
  <div class="ins-wrap">
    <aside class="side">
      <div class="sideHead">
        <div class="badge">🛡️</div>
        <div>
          <div class="sideTitle">Seguros</div>
          <div class="sideSub">Siniestros universitarios</div>
        </div>
      </div>

      <nav class="sideNav">
        <RouterLink class="sideLink" to="/insurance/overview">Resumen</RouterLink>
        <RouterLink class="sideLink" to="/insurance/coverage">Coberturas</RouterLink>
        <RouterLink class="sideLink" to="/insurance/claims">Siniestros</RouterLink>
        <RouterLink class="sideLink" to="/insurance/claims/new">Crear siniestro</RouterLink>
      </nav>

      <div class="sideFoot">
        <small class="muted">Rol: <b>{{ roleLabel }}</b></small>
      </div>
    </aside>

    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { auth } from '../../stores/auth'

const role = computed(() => String(auth.user()?.role || '').toLowerCase())
const roleLabel = computed(() => (role.value === 'admin' ? 'Administrador' : 'Seguros'))
</script>

<style scoped>
.ins-wrap{
  display:grid;
  grid-template-columns: 260px 1fr;
  gap: 16px;
  max-width: 1100px;
  margin: 0 auto;
  padding: 18px;
}
.side{
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 14px;
  height: fit-content;
  position: sticky;
  top: 78px;
}
.sideHead{
  display:flex;
  gap: 10px;
  align-items:center;
  padding-bottom: 12px;
  border-bottom: 1px solid #eef2f7;
  margin-bottom: 12px;
}
.badge{
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #eff6ff;
  display:flex;
  align-items:center;
  justify-content:center;
}
.sideTitle{ font-weight: 800; font-size: 16px; }
.sideSub{ font-size: 12px; color:#6b7280; }
.sideNav{ display:flex; flex-direction:column; gap: 8px; }
.sideLink{
  text-decoration:none;
  color:#111827;
  padding:10px 12px;
  border-radius:12px;
  border:1px solid transparent;
}
.sideLink.router-link-active{
  background:#eff6ff;
  border-color:#dbeafe;
}
.sideFoot{ margin-top: 14px; padding-top: 12px; border-top: 1px solid #eef2f7; }
.main{ min-width: 0; }

/* Mobile: apilar sidebar + contenido (evita que el layout quede a 2 columnas) */
@media (max-width: 768px){
  .ins-wrap{
    grid-template-columns: 1fr;
    gap: 12px;
    /* fuerza a ocupar el ancho real del viewport (evita que se "corra" a un lado) */
    width: 100%;
    max-width: 100%;
    margin: 0;
    padding: 12px;
  }
  .side{
    position: relative;
    top: auto;
    width: 100%;
  }
  .main{ width: 100%; }
  /* Menú lateral en fila y scroll horizontal */
  .sideNav{
        flex-direction: row;
    flex-wrap: wrap;          /* <-- en móvil, que baje a 2 líneas en vez de recortarse */
    gap: 8px;
    overflow-x: visible;      /* <-- no recortar */
    padding-bottom: 0;
}
  .sideLink{
    flex: 0 0 auto;
  }
}
</style>
