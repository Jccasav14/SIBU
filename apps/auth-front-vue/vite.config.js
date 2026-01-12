import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  // Carga envs SOLO para debug (no los redefine)
  const env = loadEnv(mode, process.cwd(), 'VITE_')

  console.log('VITE MODE:', mode)
  console.log('VITE AUTH BASE:', env.VITE_AUTH_BASE_URL)

  return {
    plugins: [vue()],
    server: {
      port: 5174,
      strictPort: true
    }
    // ❌ NO usar define para import.meta.env
  }
})
