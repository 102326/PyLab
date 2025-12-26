import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    AutoImport({
      imports: ['vue', 'vue-router', 'pinia'],
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // === 核心修复在这里 ===
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // 你的后端地址
        changeOrigin: true,
        // 下面这行是关键！把请求里的 '/api' 替换为空字符串
        // 效果：前端发 /api/auth/login -> 后端收 /auth/login
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
