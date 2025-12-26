import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useUserStore } from './user'
import { ElNotification } from 'element-plus'

export const useSocketStore = defineStore('socket', () => {
  const isConnected = ref(false)
  let socket: WebSocket | null = null
  let reconnectTimer: number | null = null

  // 建立连接
  function connect() {
    const userStore = useUserStore()
    const userId = userStore.userInfo?.id

    // 没登录或没ID，不连
    if (!userId) return

    // 已经连着，不重复连
    if (socket && socket.readyState === WebSocket.OPEN) {
      isConnected.value = true
      return
    }

    // 构造地址 (适配 ws/wss)
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    // 这里先写死后端端口，生产环境可以用 import.meta.env.VITE_WS_URL
    const wsUrl = `${protocol}://127.0.0.1:8000/ws/${userId}`

    console.log(`🔌 正在连接 WebSocket: ${wsUrl}`)
    socket = new WebSocket(wsUrl)

    socket.onopen = () => {
      console.log('✅ WebSocket 连接成功')
      isConnected.value = true
      // 连接成功，清除重连定时器
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
    }

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        handleMessage(msg)
      } catch (e) {
        // 忽略心跳包 pong
        if (event.data !== 'pong') console.error('WS消息解析失败', e)
      }
    }

    socket.onclose = (e) => {
      console.log('❌ WebSocket 断开', e.code)
      isConnected.value = false
      socket = null

      // 断线重连 (5秒后)
      if (!reconnectTimer) {
        reconnectTimer = window.setTimeout(() => {
          console.log('🔄 尝试重连...')
          connect()
        }, 5000)
      }
    }

    socket.onerror = (e) => {
      console.error('WebSocket Error', e)
    }
  }

  // 断开连接 (登出时调用)
  function disconnect() {
    if (socket) {
      socket.close()
      socket = null
    }
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    isConnected.value = false
  }

  // === 统一消息处理 ===
  async function handleMessage(msg: any) {
    const userStore = useUserStore()

    if (msg.type === 'ocr_result') {
      // 1. 弹出通知
      if (msg.status === 'success') {
        ElNotification.success({
          title: '认证通过',
          message: `恭喜！您的身份信息已核验通过。`,
          duration: 0, // 不自动关闭
        })
      } else {
        ElNotification.error({
          title: '认证失败',
          message: msg.msg || '无法识别身份证信息，请重新上传。',
          duration: 0,
        })
      }
      // 2. 核心：全局刷新用户信息
      // 这样无论你在 UserCenter 还是 Upload 页面，数据都会自动更新
      await userStore.refreshUserInfo()
    } else if (msg.type === 'system_notice') {
      ElNotification.info({
        title: '系统通知',
        message: msg.content || '收到一条新消息',
        duration: 5000,
      })
    }
  }

  return { isConnected, connect, disconnect }
})
