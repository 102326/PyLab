import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { VitePWA } from 'vite-plugin-pwa'

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
    VitePWA({
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.js',
      registerType: 'autoUpdate',
      devOptions: {
        enabled: true,
        type: 'module',
      },
      manifest: {
        name: 'PyLab Chat',
        short_name: 'PyChat',
        description: 'My Awesome Chat App',
        theme_color: '#ffffff',
        icons: [
          {
            src: 'favicon.ico',
            sizes: '64x64 32x32 24x24 16x16',
            type: 'image/x-icon',
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // === 核心修复在这里 ===
  server: {
    // host: '127.0.0.1', // 强制使用 IPv4
    // port: 5173, // 端口号
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
