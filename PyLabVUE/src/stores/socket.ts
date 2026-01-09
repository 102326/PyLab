import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useUserStore } from './user'
import { ElNotification } from 'element-plus'
import { useChatStore } from './chat'
import router from '@/router'

export const useSocketStore = defineStore('socket', () => {
  const isConnected = ref(false)
  // 用于存储最新收到的消息，供全局监听使用
  const latestMessage = ref<any>(null)

  let socket: WebSocket | null = null
  let reconnectTimer: number | null = null

  // 建立连接
  function connect() {
    const userStore = useUserStore()
    const userId = userStore.userInfo?.id

    if (!userId) return

    if (socket && socket.readyState === WebSocket.OPEN) {
      isConnected.value = true
      return
    }

    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    // 请确保这里的端口号与后端一致
    const wsUrl = `${protocol}://127.0.0.1:8000/ws/${userId}`

    console.log(`🔌 正在连接 WebSocket: ${wsUrl}`)
    socket = new WebSocket(wsUrl)

    socket.onopen = () => {
      console.log('✅ WebSocket 连接成功')
      isConnected.value = true
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
    }

    socket.onmessage = (event) => {
      try {
        if (event.data === 'pong') return
        const msg = JSON.parse(event.data)
        // 更新最新消息状态
        latestMessage.value = msg
        handleMessage(msg)
      } catch (e) {
        console.error('WS消息解析失败', e)
      }
    }

    socket.onclose = (e) => {
      console.log('❌ WebSocket 断开', e.code)
      isConnected.value = false
      socket = null

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

  // 发送消息方法
  function send(data: any) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data))
    } else {
      console.warn('Socket 未连接，消息发送失败')
    }
  }

  // === 统一消息处理 ===
  async function handleMessage(msg: any) {
    const userStore = useUserStore()
    const chatStore = useChatStore()

    if (msg.type === 'ocr_result') {
      // OCR 逻辑
      if (msg.status === 'success') {
        ElNotification.success({
          title: '认证通过',
          message: `恭喜！您的身份信息已核验通过。`,
          duration: 0,
        })
      } else {
        ElNotification.error({
          title: '认证失败',
          message: msg.msg || '无法识别身份证信息，请重新上传。',
          duration: 0,
        })
      }
      await userStore.refreshUserInfo()
    } else if (msg.type === 'system_notice') {
      // 系统通知
      ElNotification.info({
        title: '系统通知',
        message: msg.content || '收到一条新消息',
        duration: 5000,
      })
    } else if (msg.type === 'chat') {
      // 1. 添加消息到聊天记录
      chatStore.addMessage({
        sender_id: msg.from_user_id,
        receiver_id: userStore.userInfo?.id || 0,
        content: msg.content,
        created_at: msg.time,
      })

      // 2. [新增] 强制刷新联系人列表，确保左侧"最新消息"实时更新
      await chatStore.loadContacts()

      // 3. [优化] 智能通知判断逻辑
      // 条件1: 当前聊天的对象 不是 发送消息的人
      const isChattingWithOther = chatStore.currentDestId !== msg.from_user_id
      // 条件2: 浏览器当前在后台 (即使打开了对话框，人没在看)
      const isWindowHidden = document.visibilityState === 'hidden'

      if (isChattingWithOther || isWindowHidden) {
        ElNotification.info({
          title: '新消息',
          message: `收到一条新消息: ${msg.content}`,
          duration: 5000,
          // 点击通知跳转
          onClick: () => {
            // 尝试聚焦窗口
            window.focus()
            // [修复] 明确跳转路径为 /chat/user
            router.push(`/chat/user?targetId=${msg.from_user_id}`)
            ElNotification.closeAll()
          },
        })
      }
    }
  }

  return { isConnected, latestMessage, connect, disconnect, send }
})
