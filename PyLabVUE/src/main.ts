import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './assets/main.css' // <--- 确保这一行在 Element Plus 之前或之后（通常 Tailwind 放最前）
import 'element-plus/dist/index.css' // Element Plus 样式
import App from './App.vue'
import router from './router'
import { registerSW } from 'virtual:pwa-register'
const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

registerSW({
  immediate: true,
  onNeedRefresh() {
    console.log('需要刷新')
  },
  onOfflineReady() {
    console.log('离线就绪')
  },
})
