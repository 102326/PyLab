<template>
  <RouterView />

  <button
    v-if="showNotifyButton"
    @click="enableNotification"
    class="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 transition-all duration-300 animate-bounce cursor-pointer"
  >
    <span>🔔</span>
    <span>开启桌面消息提醒</span>
  </button>
  <button
    @click="goToChat"
    class="flex items-center justify-center w-14 h-14 bg-indigo-600 text-white rounded-full shadow-xl hover:bg-indigo-700 transition-all hover:scale-110 active:scale-95"
    title="打开聊天"
  >
    <span class="text-2xl">💬</span>
  </button>
</template>

<script setup lang="ts">
import { onMounted, watch, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { RouterView, useRouter } from 'vue-router'
import { useSocketStore } from '@/stores/socket'
// 引入你的 Hook
import { useBrowserNotification } from '@/composables/useBrowserNotification'
const router = useRouter()
const userStore = useUserStore()
const socketStore = useSocketStore()

const goToChat = () => {
  // 你可以根据需要跳转到具体的聊天对象的页面，这里先跳到聊天列表主页
  router.push('/chat')
}

// 1. 引入通知功能
const { permission, requestPermission, sendNotification, subscribeToPush } =
  useBrowserNotification()

// 计算属性：控制按钮显示（只有是 'default' 状态且浏览器支持时才显示）
// 'granted' = 已允许, 'denied' = 已拒绝, 'default' = 未询问
const showNotifyButton = computed(() => {
  return permission.value === 'default' && 'Notification' in window
})

// 点击按钮请求权限
const enableNotification = async () => {
  const granted = await requestPermission()
  if (granted) {
    // 1. 原地通知
    sendNotification('系统通知', { body: '通知已开启！' })

    // 2. [新增] 注册 Web Push 订阅
    // 这一步会触发浏览器向谷歌/火狐服务器注册，并把 token 发给你的后端
    await subscribeToPush()
  }
}

// 2. 核心逻辑：监听 socketStore 中的新消息
watch(
  () => socketStore.latestMessage,
  (newMessage) => {
    // 基础校验
    if (!newMessage) return

    // 可以在这里过滤消息类型，比如只处理聊天消息
    // 注意：newMessage 里的字段要和后端返回的保持一致
    if (newMessage.type === 'chat') {
      // 调用 Hook 发送通知
      // Hook 内部会自动判断：如果 document.hidden 为 false (你在看网页)，则不弹窗
      sendNotification(`收到新消息`, {
        // 如果后端没返回 senderName，就显示通用文案
        body: newMessage.content || '您有一条新消息',
        icon: '/favicon.ico',
        tag: 'chat-msg', // 标签，避免消息堆叠
        // renotify: true, // 即使标签一样，新消息来了也重新震动/提示
      })
    }
  },
  { deep: true },
)

onMounted(() => {
  userStore.initUser()

  if (userStore.token && userStore.userInfo?.id) {
    socketStore.connect()
  }
})

// 监听 Token 变化
watch(
  () => userStore.token,
  (newToken) => {
    if (newToken) {
      socketStore.connect()
    } else {
      socketStore.disconnect()
    }
  },
)
</script>

<style scoped></style>
