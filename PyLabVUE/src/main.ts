import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './assets/main.css' // <--- 确保这一行在 Element Plus 之前或之后（通常 Tailwind 放最前）
import 'element-plus/dist/index.css' // Element Plus 样式
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
