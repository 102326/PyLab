import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 1. 创建 axios 实例
const service = axios.create({
    // 如果你的 vite.config.js 配置了代理 /api，这里可以留空或者写 '/api'
    // 建议留空，这样请求 /api/xxx 会自动拼接
    baseURL: '',
    timeout: 10000 // 请求超时时间
})

// 2. 请求拦截器 (Request Interceptor)
service.interceptors.request.use(
    (config) => {
        // 从 localStorage 获取 token
        const token = localStorage.getItem('token')

        // 如果有 token，且请求不是去七牛云的（七牛云不需要我们的后端Token，它用上传凭证），则带上
        // 这里简单的判断方式：如果是发给后端 /api 的请求，就带 Token
        if (token) {
            // 标准格式：Authorization: Bearer <token>
            config.headers['Authorization'] = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// 3. 响应拦截器 (Response Interceptor)
service.interceptors.response.use(
    (response) => {
        // 2xx 范围内的状态码都会触发该函数
        return response
    },
    (error) => {
        // 超出 2xx 范围的状态码都会触发该函数
        if (error.response) {
            const status = error.response.status
            const msg = error.response.data?.detail || '请求出错'

            if (status === 401) {
                ElMessage.error('登录已过期，请重新登录')
                // 清除本地过期 token
                localStorage.removeItem('token')
                localStorage.removeItem('user_info')
                // 跳转登录页
                router.push('/login')
            } else if (status === 403) {
                ElMessage.error('没有权限执行此操作')
            } else {
                ElMessage.error(msg)
            }
        } else {
            ElMessage.error('网络连接异常')
        }
        return Promise.reject(error)
    }
)

export default service