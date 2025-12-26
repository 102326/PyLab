// src/composables/useBrowserNotification.ts
import { ref } from 'vue'

export function useBrowserNotification() {
  const isSupported = 'Notification' in window
  const permission = ref(isSupported ? Notification.permission : 'default')

  // 1. 请求权限
  const requestPermission = async () => {
    if (!isSupported) {
      console.warn('当前浏览器不支持桌面通知')
      return false
    }

    if (permission.value === 'granted') return true

    // 向用户弹出浏览器自带的询问框
    const result = await Notification.requestPermission()
    permission.value = result
    return result === 'granted'
  }

  // 2. 发送通知
  const sendNotification = (title: string, options?: NotificationOptions) => {
    // 如果不支持、没权限，或者用户当前就在看网页(网页可见)，则不发送通知
    // document.hidden 为 true 表示网页被遮挡或最小化
    if (!isSupported || permission.value !== 'granted' || !document.hidden) {
      return
    }

    // 实例化 Notification 对象，系统会自动弹出
    const notification = new Notification(title, {
      icon: '/favicon.ico', // 你的 Logo 路径
      badge: '/badge.png', // Android 任务栏图标 (可选)
      // vibrate: [200, 100, 200], // 手机端震动模式 (可选)
      ...options,
    })

    // 3. 点击通知时的交互：点击通知自动激活（聚焦）窗口
    notification.onclick = () => {
      window.focus() // 尝试聚焦窗口
      notification.close() // 点击后关闭通知

      // 这里可以加路由跳转，比如跳到对应的聊天窗口
      // router.push('/chat/123')
    }
  }

  return {
    isSupported,
    permission,
    requestPermission,
    sendNotification,
  }
}
