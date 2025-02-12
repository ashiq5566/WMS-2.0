import { fileURLToPath, URL } from 'node:url'
import path from 'path'
import Pages from 'vite-plugin-pages'
import Layouts from 'vite-plugin-vue-layouts'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), Pages(), Layouts()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  base: process.env.BUILD_ENV === 'django' ? '/static/wms-frontend' : '/',
  build: {
    outDir: process.env.BUILD_ENV === 'django' ? '../static/wms-frontend' : 'dist',
    assetsDir: '',
    manifest: 'manifest.json',
    emptyOutDir: true,
    target: 'es2015',
    chunkSizeWarningLimit: 5000,
    rollupOptions: {
      input: {
        // main: resolve('./src/main.ts')
        main: path.resolve(__dirname, './src/main.js') // Fix this line
      },
      output: {
        chunkFileNames: undefined
      }
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
