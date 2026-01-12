<template>
  <section class="card">
    <header class="head">
      <div>
        <h1>Resumen de Seguros</h1>
        <p class="muted">KPIs del módulo de siniestros (cacheado en Redis)</p>
      </div>
      <button class="btn" @click="load" :disabled="loading">Actualizar</button>
    </header>

    <p v-if="loading"><small class="muted">Cargando...</small></p>
    <p v-if="error" class="err">{{ error }}</p>

    <div v-if="overview" class="grid">
      <div class="kpi">
        <div class="kpiLabel">Total siniestros</div>
        <div class="kpiValue">{{ totalClaims }}</div>
      </div>

      <div class="kpi">
        <div class="kpiLabel">Total pagado</div>
        <div class="kpiValue">$ {{ totalPaid }}</div>
      </div>

      <div class="kpi" v-for="(v, k) in statusCounts" :key="k">
        <div class="kpiLabel">Estado: {{ k }}</div>
        <div class="kpiValue">{{ v }}</div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getOverview } from '../../services/claimsApi'

const loading = ref(false)
const error = ref('')
const overview = ref(null)

const totalClaims = computed(() => overview.value?.total_claims ?? overview.value?.total ?? overview.value?.totalClaims ?? 0)
const totalPaid = computed(() => overview.value?.total_paid_amount ?? overview.value?.totalPaidAmount ?? overview.value?.total_paid ?? 0)
const statusCounts = computed(() => overview.value?.status_counts ?? overview.value?.counts_by_status ?? overview.value?.statusCounts ?? {})

async function load(){
  loading.value = true
  error.value = ''
  try{
    overview.value = await getOverview()
  }catch(e){
    error.value = String(e?.message || e)
  }finally{
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.card{
  background:#fff;
  border:1px solid #e5e7eb;
  border-radius:14px;
  padding: 16px;
}
.head{
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  gap: 12px;
  margin-bottom: 12px;
}
h1{ margin:0; font-size: 20px; }
.grid{
  display:grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}
.kpi{
  border:1px solid #eef2f7;
  border-radius: 14px;
  padding: 12px;
  background:#fafafa;
}
.kpiLabel{ color:#6b7280; font-size: 12px; }
.kpiValue{ font-size: 22px; font-weight: 800; margin-top: 6px; }
.btn{
  background:#2563eb;
  color:#fff;
  border:none;
  padding: 10px 12px;
  border-radius: 12px;
  cursor:pointer;
}
.btn:disabled{ opacity:.6; cursor:not-allowed; }
.err{ color:#b91c1c; }

@media (max-width: 768px){
  /* En mobile evita que el botón se “salga” por falta de espacio */
  .head{
    flex-direction: column;
    align-items: stretch;
  }
  .btn{
    width: 100%;
  }
}
</style>
