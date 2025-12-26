import axios, { type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 1. 创建 Axios 实例
const service = axios.create({
  // 这里的 '/api' 会被 vite.config.ts 中的 proxy 代理到 localhost:8000
  baseURL: '/api',
  timeout: 10000,
})

// 2. 请求拦截器：自动携带 Token
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 3. 响应拦截器：统一处理错误
service.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: any) => {
    let msg = '请求出错'

    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      msg = data?.detail || error.message

      // 401: Token 过期
      if (status === 401) {
        ElMessage.error('登录已过期，请重新登录')
        localStorage.removeItem('token')
        localStorage.removeItem('user_info')
        router.push('/login')
      }
      // 422: 参数校验错误 (FastAPI 常用)
      else if (status === 422) {
        msg = '参数校验失败，请检查输入'
        if (data?.detail && Array.isArray(data.detail)) {
          const firstErr = data.detail[0]
          msg = `${firstErr.loc.join('.')} : ${firstErr.msg}`
        }
        ElMessage.warning(msg)
      } else {
        ElMessage.error(msg)
      }
    } else {
      ElMessage.error('网络连接异常，请检查后端服务')
    }
    return Promise.reject(error)
  },
)

export default service
