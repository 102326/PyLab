// src/composables/useBrowserNotification.ts
import { ref } from 'vue'
import request from '@/utils/request' // 引入封装好的 axios 实例

// 工具函数：将 Base64 字符串转为 Uint8Array
// (浏览器 Push API 要求 applicationServerKey 必须是这种二进制格式)
function urlBase64ToUint8Array(base64String: string) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

export function useBrowserNotification() {
  const isSupported = 'Notification' in window && 'serviceWorker' in navigator
  const permission = ref(isSupported ? Notification.permission : 'default')

  // 1. 请求权限
  const requestPermission = async () => {
    if (!isSupported) {
      console.warn('当前浏览器不支持桌面通知或 Service Worker')
      return false
    }

    if (permission.value === 'granted') return true

    const result = await Notification.requestPermission()
    permission.value = result
    return result === 'granted'
  }

  // 2. 发送前台通知
  const sendNotification = (title: string, options?: NotificationOptions) => {
    if (!isSupported || permission.value !== 'granted' || !document.hidden) {
      return
    }

    const notification = new Notification(title, {
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      ...options,
    })

    notification.onclick = () => {
      window.focus()
      notification.close()
    }
  }

  // 3. [新增] 注册 Web Push 订阅
  const subscribeToPush = async () => {
    if (!isSupported) return

    try {
      // 等待 Service Worker 准备就绪
      const registration = await navigator.serviceWorker.ready

      // 检查浏览器是否已经有订阅
      let subscription = await registration.pushManager.getSubscription()

      // 如果没有订阅，则发起新订阅
      if (!subscription) {
        // 第一步：从后端获取公钥
        const res = await request.get('/notifications/vapid-public-key')
        const publicKey = res.data.publicKey

        if (!publicKey) {
          console.error('无法获取 VAPID 公钥')
          return
        }

        // 第二步：转换公钥格式
        const convertedVapidKey = urlBase64ToUint8Array(publicKey)

        // 第三步：向浏览器厂商注册
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: convertedVapidKey,
        })
      }

      // 第四步：把订阅信息发给后端存起来
      await request.post('/notifications/subscribe', subscription.toJSON())

      console.log('✅ Web Push 订阅成功')
      return subscription
    } catch (error) {
      console.error('❌ Web Push 订阅失败:', error)
    }
  }

  return {
    isSupported,
    permission,
    requestPermission,
    sendNotification,
    subscribeToPush, // <--- 关键！一定要在这里导出
  }
}
