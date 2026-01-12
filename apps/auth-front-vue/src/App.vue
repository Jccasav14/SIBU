<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import NavBar from "./components/NavBar.vue";

const route = useRoute();

const isAuthRoute = computed(() => ["/login", "/register"].includes(route.path));
const showNavbar = computed(() => !isAuthRoute.value);
</script>

<template>
  <NavBar v-if="showNavbar" />

  <!-- Layout consistente para todas las vistas internas -->
  <main v-if="showNavbar" class="app-shell">
    <div class="app-container">
      <router-view />
    </div>
  </main>

  <!-- Auth screens usan su propio layout a pantalla completa -->
  <router-view v-else />
</template>
