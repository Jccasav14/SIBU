    <template>
    <div class="admin-view">
        <!-- HEADER -->
        <header class="admin-header">
        <h1>Panel Administrador</h1>
        <p class="subtitle">Bienvenido administrador</p>
        </header>

        <!-- CONTENIDO -->
        <section class="admin-content">
        <!-- Aquí va todo el contenido real del admin -->
        <AdminTab />
        </section>
    </div>
    </template>

    <script setup>
    import AdminTab from './AdminTab.vue'
    </script>

    <style scoped>
    .admin-view {
    padding: 0;
    }

    .admin-header {
    margin-bottom: 2rem;
    }

    .admin-header h1 {
    margin: 0;
    font-size: 2rem;
    }

    .subtitle {
    color: #666;
    margin-top: 0.5rem;
    }

    .admin-content {
    margin-top: 1.5rem;
    }
    </style>
