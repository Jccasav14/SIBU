<template>
  <header class="nav">
    <div class="inner">
      <div class="leftGroup">
        <!-- Brand -->
        <div class="brand" @click="goHome">
          <div class="logoBadge">S</div>
          <div class="brandText">
            <div class="title">SIBU</div>
            <div class="sub">Bienestar Universitario</div>
          </div>
        </div>

        <!-- Desktop nav (módulos) -->
        <nav v-if="isAuthed" class="mainNav" aria-label="Main">
          <!-- Admin / Professional modules -->
          <template v-if="!isInsurance">
            <RouterLink class="navLink" to="/cases">Casos</RouterLink>
            <RouterLink class="navLink" to="/agenda">Citas</RouterLink>
            <RouterLink class="navLink" to="/reports">Reportes</RouterLink>
            <RouterLink v-if="isAdmin" class="navLink" to="/admin">Admin</RouterLink>
            <RouterLink v-if="isAdmin" class="navLink" to="/insurance/overview">Seguros</RouterLink>
          </template>

          <!-- Insurance module -->
          <template v-else>
            <RouterLink class="navLink" to="/insurance/overview">Seguros</RouterLink>
          </template>
        </nav>

        <!-- Mobile menu button (solo móvil, por CSS) -->
        <button
          v-if="isAuthed"
          class="mobileMenuBtn"
          type="button"
          aria-label="Abrir menú"
          @click="toggleMobileNav"
          ref="mobileBtnRef"
        >
          ☰
        </button>
      </div>

      <!-- Right: usuario -->
      <div class="right">
        <template v-if="!isAuthed">
          <RouterLink class="link ghost" to="/login">Iniciar sesión</RouterLink>
          <RouterLink class="btn" to="/register">Crear cuenta</RouterLink>
        </template>

        <template v-else>
          <button class="userBtn" @click="toggleUserMenu" ref="userBtnRef" type="button">
            <span class="avatar">{{ initials }}</span>
            <span class="who">
              <span class="name">{{ displayName }}</span>
              <span class="role">{{ roleLabel }}</span>
            </span>
          </button>

          <!-- Dropdown usuario -->
          <div v-if="userMenuOpen" class="menu" ref="userMenuRef">
            <button class="menuItem" @click="goProfile">Perfil</button>
            <button class="menuItem" @click="goChangePassword">Cambiar contraseña</button>
            <div class="divider"></div>
            <button class="menuItem danger" @click="logout">Cerrar sesión</button>
          </div>
        </template>
      </div>
    </div>

    <!-- Overlay + panel mobile -->
    <div v-if="mobileNavOpen" class="mobileOverlay" @click="closeMobileNav"></div>

    <div v-if="mobileNavOpen" class="mobilePanel" ref="mobilePanelRef">
      <div class="mobilePanelHeader">
        <div class="mobileTitle">Menú</div>
        <button class="mobileClose" type="button" aria-label="Cerrar menú" @click="closeMobileNav">✕</button>
      </div>

      <div class="mobileLinks">
        <template v-if="!isInsurance">
          <RouterLink class="mobileLink" to="/cases" @click="closeMobileNav">Casos</RouterLink>
          <RouterLink class="mobileLink" to="/agenda" @click="closeMobileNav">Citas</RouterLink>
          <RouterLink class="mobileLink" to="/reports" @click="closeMobileNav">Reportes</RouterLink>
          <RouterLink v-if="isAdmin" class="mobileLink" to="/admin" @click="closeMobileNav">Admin</RouterLink>
          <RouterLink v-if="isAdmin" class="mobileLink" to="/insurance/overview" @click="closeMobileNav">Seguros</RouterLink>
        </template>

        <template v-else>
          <RouterLink class="mobileLink" to="/insurance/overview" @click="closeMobileNav">Seguros</RouterLink>
        </template>

        <div class="mobileDivider"></div>

        <button class="mobileAction" @click="goProfile">Perfil</button>
        <button class="mobileAction" @click="goChangePassword">Cambiar contraseña</button>
        <button class="mobileAction danger" @click="logout">Cerrar sesión</button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { auth } from "../stores/auth";

const router = useRouter();
const route = useRoute();

const isAuthed = computed(() => auth.isAuthenticated());
const user = computed(() => auth.user() || null);

const role = computed(() => String(user.value?.role || "").toLowerCase());
const isAdmin = computed(() => role.value === "admin");
const isPro = computed(() => role.value === "professional");
const isInsurance = computed(() => role.value === "insurance");

const roleLabel = computed(() => {
  if (isAdmin.value) return "Admin";
  if (isPro.value) return "Profesional";
  if (isInsurance.value) return "Seguros";
  return "Usuario";
});

const displayName = computed(() => user.value?.email || "Usuario");

const initials = computed(() => {
  const v = (displayName.value || "").trim();
  if (!v) return "U";
  const parts = v.split(/\s+/).filter(Boolean);
  const a = parts[0]?.[0] || "U";
  const b = parts.length > 1 ? (parts[1]?.[0] || "") : "";
  return (a + b).toUpperCase();
});

/** User dropdown **/
const userMenuOpen = ref(false);
const userBtnRef = ref<HTMLElement | null>(null);
const userMenuRef = ref<HTMLElement | null>(null);

/** Mobile nav **/
const mobileNavOpen = ref(false);
const mobileBtnRef = ref<HTMLElement | null>(null);
const mobilePanelRef = ref<HTMLElement | null>(null);

function goHome() {
  router.push(isAuthed.value ? "/dashboard" : "/");
}

function toggleUserMenu() {
  userMenuOpen.value = !userMenuOpen.value;
  // si abres user menu, cierra el mobile nav por seguridad
  if (userMenuOpen.value) mobileNavOpen.value = false;
}
function closeUserMenu() {
  userMenuOpen.value = false;
}

function toggleMobileNav() {
  mobileNavOpen.value = !mobileNavOpen.value;
  // si abres mobile nav, cierra user menu por seguridad
  if (mobileNavOpen.value) userMenuOpen.value = false;
}
function closeMobileNav() {
  mobileNavOpen.value = false;
}

function goProfile() {
  closeUserMenu();
  closeMobileNav();
  if (isAdmin.value) router.push("/admin");
  else if (isPro.value) router.push("/professional");
  else if (isInsurance.value) router.push("/insurance/overview");
  else router.push("/me");
}

function goChangePassword() {
  closeUserMenu();
  closeMobileNav();
  router.push("/change-password");
}

function logout() {
  closeUserMenu();
  closeMobileNav();
  auth.logout();
  router.push("/login");
}

function onDocClick(e: MouseEvent) {
  const t = e.target as Node;

  // user menu outside click
  if (userMenuOpen.value) {
    const inBtn = !!userBtnRef.value && userBtnRef.value.contains(t);
    const inMenu = !!userMenuRef.value && userMenuRef.value.contains(t);
    if (!inBtn && !inMenu) userMenuOpen.value = false;
  }

  // mobile panel outside click handled by overlay, but close if click outside panel without overlay (safety)
  if (mobileNavOpen.value) {
    const inBtn = !!mobileBtnRef.value && mobileBtnRef.value.contains(t);
    const inPanel = !!mobilePanelRef.value && mobilePanelRef.value.contains(t);
    if (!inBtn && !inPanel) mobileNavOpen.value = false;
  }
}

onMounted(() => {
  document.addEventListener("click", onDocClick, true);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", onDocClick, true);
});

// close menus on route change
onMounted(() => {
  // simple reactive close when path changes
  // (route is reactive; this runs whenever component is created)
});
</script>

<style scoped>
.nav {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: #0b1220;
  color: #fff;
  border-bottom: 1px solid rgba(255,255,255,.08);
}

.inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  gap: 16px;
}

.leftGroup {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.logoBadge {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,.12);
  font-weight: 800;
}

.brandText .title {
  font-weight: 800;
  line-height: 1;
}
.brandText .sub {
  font-size: 12px;
  opacity: .75;
  line-height: 1.2;
}

.mainNav {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: nowrap;
  overflow: hidden;
}

.navLink {
  color: rgba(255,255,255,.9);
  text-decoration: none;
  padding: 8px 10px;
  border-radius: 10px;
  white-space: nowrap;
}
.navLink.router-link-active {
  background: rgba(255,255,255,.12);
}

.right {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
}

.link {
  color: rgba(255,255,255,.9);
  text-decoration: none;
}
.link.ghost {
  opacity: .9;
}

.btn {
  background: #3b82f6;
  color: #fff;
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 12px;
  font-weight: 700;
}

.userBtn {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255,255,255,.10);
  border: 1px solid rgba(255,255,255,.10);
  color: #fff;
  padding: 8px 10px;
  border-radius: 14px;
  cursor: pointer;
}
.avatar {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: rgba(255,255,255,.16);
  font-weight: 800;
}
.who {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.1;
}
.name {
  font-weight: 800;
  font-size: 12px;
}
.role {
  font-size: 11px;
  opacity: .8;
}

.menu {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: 220px;
  background: #0f172a;
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 16px;
  box-shadow: 0 22px 60px rgba(0,0,0,.45);
  padding: 8px;
}
.menuItem {
  width: 100%;
  text-align: left;
  padding: 10px 10px;
  border-radius: 12px;
  background: transparent;
  border: 0;
  color: rgba(255,255,255,.92);
  cursor: pointer;
}
.menuItem:hover {
  background: rgba(255,255,255,.08);
}
.menuItem.danger {
  color: #ffb4b4;
}
.divider {
  height: 1px;
  background: rgba(255,255,255,.10);
  margin: 6px 4px;
}

/* Mobile menu button */
.mobileMenuBtn {
  display: none; /* default hidden; shown in mobile via media query */
  background: rgba(255,255,255,.10);
  border: 1px solid rgba(255,255,255,.10);
  color: #fff;
  padding: 8px 10px;
  border-radius: 14px;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

/* Overlay + panel mobile (NO transparente) */
.mobileOverlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  z-index: 9998;
}

.mobilePanel {
  position: fixed;
  top: 64px;
  right: 12px;
  width: min(340px, calc(100vw - 24px));
  background: #ffffff;
  color: #0b1220;
  border: 1px solid rgba(15, 23, 42, .12);
  border-radius: 18px;
  box-shadow: 0 22px 60px rgba(0,0,0,.25);
  padding: 10px;
  z-index: 9999;
}

.mobilePanelHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 6px 10px;
}

.mobileTitle {
  font-weight: 900;
}

.mobileClose {
  background: rgba(15,23,42,.06);
  border: 1px solid rgba(15,23,42,.10);
  border-radius: 12px;
  padding: 6px 10px;
  cursor: pointer;
}

.mobileLinks {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 6px 8px;
}

.mobileLink {
  text-decoration: none;
  color: #0b1220;
  padding: 10px 10px;
  border-radius: 14px;
  background: rgba(15,23,42,.04);
}
.mobileLink:active {
  transform: translateY(1px);
}

.mobileDivider {
  height: 1px;
  background: rgba(15,23,42,.10);
  margin: 6px 2px;
}

.mobileAction {
  width: 100%;
  text-align: left;
  padding: 10px 10px;
  border-radius: 14px;
  background: rgba(15,23,42,.04);
  border: 0;
  cursor: pointer;
  color: #0b1220;
}
.mobileAction.danger {
  background: rgba(255, 76, 76, .10);
  color: #b00020;
}

/* Responsive rules */
@media (max-width: 768px) {
  .mainNav { display: none; }
  .mobileMenuBtn { display: inline-flex; align-items: center; justify-content: center; }
  .brandText .sub { display: none; } /* optional: reduce height */
}
</style>
