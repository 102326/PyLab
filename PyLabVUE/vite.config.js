import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    // 默认端口 5173
    port: 5173,
    proxy: {
      // 捕获所有以 /api 开头的请求
      '/api': {
        // 转发目标: FastAPI 后端地址
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // 路径重写: 把 /api 去掉，变成 /auth/dingtalk/login 发给后端
        // 因为你的后端路由是 defined at /auth (app/Views/auth.py)
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
})
