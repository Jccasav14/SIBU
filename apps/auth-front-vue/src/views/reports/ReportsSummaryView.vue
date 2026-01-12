<template>
  <section class="reports-summary">
    <header class="toolbar">
      <h2>Resumen</h2>

      <div class="filters">
        <select v-model="window" class="select" @change="load">
          <option value="24h">24h</option>
          <option value="7d">7d</option>
          <option value="30d">30d</option>
        </select>

        <button class="btn" @click="load">Actualizar</button>
      </div>
    </header>

    <div class="cards">
      <div class="card">
        <h4>Servicios</h4>
        <p>{{ totalsList.length }}</p>
      </div>

      <div class="card">
        <h4>Eventos</h4>
        <p>{{ totalEvents }}</p>
      </div>
    </div>

    <section class="block">
      <h3>Totales por servicio</h3>
      <table class="table">
        <thead>
          <tr>
            <th>Servicio</th>
            <th>Eventos</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(t, i) in totalsList" :key="i">
            <td>{{ t.service }}</td>
            <td>{{ t.count }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="block">
      <h3>Top actores</h3>
      <table class="table">
        <thead>
          <tr>
            <th>Actor</th>
            <th>Rol</th>
            <th>Eventos</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(a, i) in topActors" :key="i">
            <td>{{ a.actor }}</td>
            <td>{{ a.role || 'unknown' }}</td>
            <td>{{ a.count }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getReportsSummary } from '../../services/reportsApi'

const window = ref('7d')

const summary = ref({
  totals_by_service: [],
  top_actors: []
})

const totalsList = computed(() =>
  Array.isArray(summary.value.totals_by_service)
    ? summary.value.totals_by_service
    : []
)

const topActors = computed(() =>
  Array.isArray(summary.value.top_actors)
    ? summary.value.top_actors
    : []
)

const totalEvents = computed(() =>
  totalsList.value
    .map(t => Number(t?.count || 0))
    .reduce((a, b) => a + b, 0)
)

async function load () {
  summary.value = await getReportsSummary(window.value)
}

onMounted(load)
</script>

<style scoped>
.reports-summary {
  padding: 1rem;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filters {
  display: flex;
  gap: 0.5rem;
}

.cards {
  display: flex;
  gap: 1rem;
  margin: 1rem 0;
}

.card {
  background: #fff;
  padding: 1rem;
  border-radius: 8px;
  min-width: 140px;
}

.block {
  margin-top: 1.5rem;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 0.5rem;
  border-bottom: 1px solid #eee;
}
</style>
