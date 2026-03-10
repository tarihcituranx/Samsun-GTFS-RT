import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";
import { VitePWA } from "vite-plugin-pwa";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    hmr: {
      overlay: false,
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  },
  plugins: [
    react(),
    mode === "development" && componentTagger(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,jpg,jpeg,mp3}'],
        runtimeCaching: [
          {
            urlPattern: /api\/(tum_duraklar|hat|samair|odak)/,
            handler: 'NetworkFirst',
            options: { cacheName: 'api-cache' }
          }
        ]
      },
      manifest: {
        name: "Kentli — Şehrinin Rehberi",
        short_name: "Kentli",
        description: "Samsun toplu taşıma hatları, canlı araç takibi ve güzergah planlama.",
        theme_color: "#020617",
        background_color: "#020617",
        display: "standalone",
        icons: [
          {
            src: "/static/images/samulas.png",
            sizes: "192x192",
            type: "image/png"
          },
          {
            src: "/static/images/sbb.png",
            sizes: "512x512",
            type: "image/png"
          }
        ]
      }
    })
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
