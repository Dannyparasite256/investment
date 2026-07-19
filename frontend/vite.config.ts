import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'CryptoInvest',
        short_name: 'CryptoInvest',
        description: 'Premium cryptocurrency investment platform',
        theme_color: '#09090B',
        background_color: '#09090B',
        display: 'standalone',
        start_url: '/app/',
        icons: [
          {
            src: '/favicon.svg',
            sizes: 'any',
            type: 'image/svg+xml',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        navigateFallback: '/index.html',
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        // Force clients to pick up new asset hashes after deploy
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: true,
        // Load push/notificationclick handlers for VAPID web push (served from dist root)
        importScripts: ['push-handler.js'],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  // Dev: '/'. Production (Django /app/): VITE_BASE=/app/ npm run build
  base: process.env.VITE_BASE || '/',
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
